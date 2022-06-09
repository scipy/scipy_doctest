import re
import warnings
import doctest
from doctest import NORMALIZE_WHITESPACE, ELLIPSIS, IGNORE_EXCEPTION_DETAIL

import numpy as np

from . import _util

class DTConfig:
    """A bag class to collect various configuration bits. 

    If an attribute is None, helpful defaults are subsituted. If defaults
    are not sufficient, users should create an instance of this class,
    override the desired attributes and pass the instance to `testmod`.

    Attributes
    ----------
    default_namespace : dict
        The namespace to run examples in.
    check_namespace : dict
        The namespace to do checks in.
    rndm_markers : set
        Additional directives which act like `# doctest: + SKIP`.
    atol : float
    rtol : float
        Absolute and relative tolerances to check doctest examples with. 
        Specifically, the check is ``np.allclose(want, got, atol=atol, rtol=rtol)``
    optionflags : int
        doctest optionflags
        Default is ``NORMALIZE_WHITESPACE | ELLIPSIS | IGNORE_EXCEPTION_DETAIL``
    stopwords : list
        If an example contains any of these stopwords, do not check the output
        (but do check that the source is valid python).
    skiplist : set
        A list of names which are known to fail doctesting and we like to keep
        it that way e.g. sometimes pseudocode is acceptable etc.
    user_context_mgr
        A context manager to run tests in. Is entered for each DocTest
        (for API docs, this is typically a single docstring). The operation is
        roughly

        >>> for test in tests:
        ...     with user_context():
        ...         runner.run(test)
        Default is a noop.

    parse_namedtuples : bool
        Whether to compare e.g. ``TTestResult(pvalue=0.9, statistic=42)``
        literally or extract the numbers and compare the tuple ``(0.9, 42)``.
        Default is True.
    nameerror_after_exception : bool
        If an example fails, next examples in the same test may raise spurious
        NameErrors. Set to True if you want to see these, or if your test
        is actually expected to raise NameErrors. 
        Default is False.

    """
    def __init__(self, *, # DTChecker configuration
                          default_namespace=None,
                          check_namespace=None,
                          rndm_markers=None,
                          atol=1e-8,
                          rtol=1e-2,
                          # DTRunner configuration
                          optionflags=None,
                          # DTFinder/DTParser configuration
                          stopwords=None,
                          skiplist=None,
                          # Additional user configuration
                          user_context_mgr=None,
                          # Obscure switches
                          parse_namedtuples=True,  # Checker
                          nameerror_after_exception=False,  # Runner
    ):
        ### DTChecker configuration ###
        # The namespace to run examples in
        if default_namespace is None:
            default_namespace = {'np': np}
        self.default_namespace = default_namespace

        # The namespace to do checks in
        if check_namespace is None:
            check_namespace = {
                  'np': np,
                  'assert_allclose': np.testing.assert_allclose,
                  'assert_equal': np.testing.assert_equal,
                  # recognize numpy repr's
                  'array': np.array,
                  'matrix': np.matrix,
                  'masked_array': np.ma.masked_array,
                  'int64': np.int64,
                  'uint64': np.uint64,
                  'int8': np.int8,
                  'int32': np.int32,
                  'float32': np.float32,
                  'float64': np.float64,
                  'dtype': np.dtype,
                  'nan': np.nan,
                  'NaN': np.nan,
                  'inf': np.inf,
                  'Inf': np.inf,}
            self.check_namespace = check_namespace

        # Additional directives which act like `# doctest: + SKIP`
        if rndm_markers is None:
            rndm_markers = {'# random', '# Random',
                            '#random', '#Random',
                            "# may vary"}
        self.rndm_markers = rndm_markers

        self.atol, self.rtol = atol, rtol

        ### DTRunner configuration ###

        # doctest optionflags
        if optionflags is None:
            optionflags = NORMALIZE_WHITESPACE | ELLIPSIS | IGNORE_EXCEPTION_DETAIL
        self.optionflags = optionflags

        ### DTFinder/DTParser configuration ###
        # ignore examples which contain any of these stopwords
        if stopwords is None:
            stopwords = {'plt.', '.hist', '.show', '.ylim', '.subplot(',
                 'set_title', 'imshow', 'plt.show', '.axis(', '.plot(',
                 '.bar(', '.title', '.ylabel', '.xlabel', 'set_ylim', 'set_xlim',
                 '# reformatted', '.set_xlabel(', '.set_ylabel(', '.set_zlabel(',
                 '.set(xlim=', '.set(ylim=', '.set(xlabel=', '.set(ylabel=', '.xlim('}
        self.stopwords = stopwords

        # these names are known to fail doctesting and we like to keep it that way
        # e.g. sometimes pseudocode is acceptable etc
        if skiplist is None:
            skiplist = set(['scipy.special.sinc',  # comes from numpy
                            'scipy.misc.who',  # comes from numpy
                            'scipy.optimize.show_options',])
        self.skiplist = skiplist

        #### User configuration
        if user_context_mgr is None:
            user_context_mgr = _util.noop_context_mgr
        self.user_context_mgr = user_context_mgr

        #### Obscure switches, best leave intact
        self.parse_namedtuples = parse_namedtuples
        self.nameerror_after_exception = nameerror_after_exception


def try_convert_namedtuple(got):
    # suppose that "got" is smth like MoodResult(statistic=10, pvalue=0.1).
    # Then convert it to the tuple (10, 0.1), so that can later compare tuples.
    num = got.count('=')
    if num == 0:
        # not a nameduple, bail out
        return got
    regex = (r'[\w\d_]+\(' +
             ', '.join([r'[\w\d_]+=(.+)']*num) +
             r'\)')
    grp = re.findall(regex, " ".join(got.split()))
    # fold it back to a tuple
    got_again = '(' + ', '.join(grp[0]) + ')'
    return got_again


class DTChecker(doctest.OutputChecker):
    obj_pattern = re.compile(r'at 0x[0-9a-fA-F]+>')
    vanilla = doctest.OutputChecker()

    def __init__(self, config=None):

        if config is None:
            config = DTConfig()
        self.config = config

        self.parse_namedtuples = self.config.parse_namedtuples
        self.atol, self.rtol = self.config.atol, self.config.rtol
        self.ns = dict(self.config.check_namespace)
        self.rndm_markers = set(self.config.rndm_markers)
        self.rndm_markers.add('# _ignore')  # technical, private. See DTParser


    def check_output(self, want, got, optionflags):
        # cut it short if they are equal
        if want == got:
            return True

        # skip random stuff
        if any(word in want for word in self.rndm_markers):
            return True

        # skip function/object addresses
        if self.obj_pattern.search(got):
            return True

        # ignore comments (e.g. signal.freqresp)
        if want.lstrip().startswith("#"):
            return True

        # try the standard doctest
        try:
            if self.vanilla.check_output(want, got, optionflags):
                return True
        except Exception:
            pass

        # OK then, convert strings to objects
        try:
            a_want = eval(want, dict(self.ns))
            a_got = eval(got, dict(self.ns))
        except Exception:
            # Maybe we're printing a numpy array? This produces invalid python
            # code: `print(np.arange(3))` produces "[0 1 2]" w/o commas between
            # values. So, reinsert commas and retry.
            # TODO: handle (1) abberivation (`print(np.arange(10000))`), and
            #              (2) n-dim arrays with n > 1
            s_want = want.strip()
            s_got = got.strip()
            cond = (s_want.startswith("[") and s_want.endswith("]") and
                    s_got.startswith("[") and s_got.endswith("]"))
            if cond:
                s_want = ", ".join(s_want[1:-1].split())
                s_got = ", ".join(s_got[1:-1].split())
                return self.check_output(s_want, s_got, optionflags)

            # maybe we are dealing with masked arrays?
            # their repr uses '--' for masked values and this is invalid syntax
            # If so, replace '--' by nans (they are masked anyway) and retry
            if 'masked_array' in want or 'masked_array' in got:
                s_want = want.replace('--', 'nan')
                s_got = got.replace('--', 'nan')
                return self.check_output(s_want, s_got, optionflags)

            if "=" not in want and "=" not in got:
                # if we're here, want and got cannot be eval-ed (hence cannot
                # be converted to numpy objects), they are not namedtuples
                # (those must have at least one '=' sign).
                # Thus they should have compared equal with vanilla doctest.
                # Since they did not, it's an error.
                return False

            if not self.parse_namedtuples:
                return False
            # suppose that "want"  is a tuple, and "got" is smth like
            # MoodResult(statistic=10, pvalue=0.1).
            # Then convert the latter to the tuple (10, 0.1),
            # and then compare the tuples.
            try:
                got_again = try_convert_namedtuple(got)
                want_again = try_convert_namedtuple(want)
            except Exception:
                return False
            else:
                return self.check_output(want_again, got_again, optionflags)


        # ... and defer to numpy
        try:
            return self._do_check(a_want, a_got)
        except Exception:
            # heterog tuple, eg (1, np.array([1., 2.]))
            try:
                return all(self._do_check(w, g) for w, g in zip(a_want, a_got))
            except (TypeError, ValueError):
                return False

    def _do_check(self, want, got):
        # This should be done exactly as written to correctly handle all of
        # numpy-comparable objects, strings, and heterogeneous tuples
        try:
            if want == got:
                return True
        except Exception:
            pass
        with warnings.catch_warnings():
            # NumPy's ragged array deprecation of np.array([1, (2, 3)])
            warnings.simplefilter('ignore', np.VisibleDeprecationWarning)

            # This line is the crux of the whole thing. The rest is mostly scaffolding.
            result = np.allclose(want, got, atol=self.atol, rtol=self.rtol)
        return result


class DTRunner(doctest.DocTestRunner):
    DIVIDER = "\n"

    def __init__(self, checker=None, verbose=None, optionflags=None, config=None):
        if config is None:
            config = DTConfig()
        if checker is None:
            checker = DTChecker(config)
        self.nameerror_after_exception = config.nameerror_after_exception
        if optionflags is None:
            optionflags = config.optionflags
        doctest.DocTestRunner.__init__(self, checker=checker, verbose=verbose,
                                       optionflags=optionflags)

    def _report_item_name(self, out, item_name, new_line=False):
        if item_name is not None:
            out("\n " + item_name + "\n " + "-"*len(item_name))
            if new_line:
                out("\n")

    def report_start(self, out, test, example):
        self._checker._source = example.source
        return doctest.DocTestRunner.report_start(self, out, test, example)

    def report_success(self, out, test, example, got):
        if self._verbose:
            self._report_item_name(out, test.name, new_line=True)
        return doctest.DocTestRunner.report_success(self, out, test, example, got)

    def report_unexpected_exception(self, out, test, example, exc_info):
        if not self.nameerror_after_exception:
            # Ignore name errors after failing due to an unexpected exception
            # NB: this came in in https://github.com/scipy/scipy/pull/13116
            # However, here we attach the flag to the test itself, not the runner
            if not hasattr(test, 'had_unexpected_error'):
                test.had_unexpected_error = True
            else:
                exception_type = exc_info[0]
                if exception_type is NameError:
                    return
        self._report_item_name(out, test.name)
        return super().report_unexpected_exception(out, test, example, exc_info)

    def report_failure(self, out, test, example, got):
        self._report_item_name(out, test.name)
        return doctest.DocTestRunner.report_failure(self, out, test,
                                                    example, got)

    def get_history(self):
        """Return a dict with names of items which were run.

        Actually the dict is `{name : (f, t)}`, where `name` is the name of
        an object, and the value is a tuple of the numbers of examples which
        failed and which were tried.
        """
        return self._name2ft


class DebugDTRunner(DTRunner):
    """Doctest runner which raises on a first error.

    Almost verbatim copy of `doctest.DebugRunner`.
    """
    def run(self, test, compileflags=None, out=None, clear_globs=True):
        r = super().run(test, compileflags, out, False)
        if clear_globs:
            test.globs.clear()
        return r

    def report_unexpected_exception(self, out, test, example, exc_info):
        raise doctest.UnexpectedException(test, example, exc_info)

    def report_failure(self, out, test, example, got):
        raise doctest.DocTestFailure(test, example, got)


class DTFinder(doctest.DocTestFinder):
    """A Finder with a stopword list.
    """
    def find(self, obj, name=None, module=None, globs=None, extraglobs=None, config=None):
        if config is None:
            config = DTConfig()
        if globs is None:
            globs = dict(config.default_namespace)
        tests = super().find(obj, name, module, globs, extraglobs)

        for test in tests:
            for example in test.examples:
                if any(word in example.source for word in config.stopwords):
                    # Found a stopword. Do not check the output (but do check
                    # that the source is valid python). 
                    example.want += "  # _ignore\n"
        return tests


class DTParser(doctest.DocTestParser):
    """A Parser with a stopword list.
    """
    def get_examples(self, string, name='<string>', config=None):
        if config is None:
            config = DTConfig()
        stopwords = config.stopwords

        examples = []
        for example in self.parse(string, name):
            # .parse returns a list of examples and intervening text
            if not isinstance(example, doctest.Example):
                continue
            if any(word in example.source for word in stopwords):
                # Found a stopword. Do not check the output (but do check
                # that the source is valid python). 
                example.want += "  # _ignore\n"
            examples.append(example)
        return examples

