import re
import warnings
import inspect
import doctest
from doctest import NORMALIZE_WHITESPACE, ELLIPSIS, IGNORE_EXCEPTION_DETAIL
from itertools import zip_longest

import numpy as np

from . import util

# Register the optionflag to skip whole blocks, i.e.
# sequences of Examples without an intervening text.
SKIPBLOCK = doctest.register_optionflag('SKIPBLOCK')


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
    strict_check : bool
       Whether to check that dtypes match or rely on the lax definition of
       equality of numpy objects. For instance, `3 == np.float64(3)`, but
       dtypes do not match.
       Default is False.
    optionflags : int
        doctest optionflags
        Default is ``NORMALIZE_WHITESPACE | ELLIPSIS | IGNORE_EXCEPTION_DETAIL``
    stopwords : set
        If an example contains any of these stopwords, do not check the output
        (but do check that the source is valid python).
    pseudocode : list
        List of strings. If an example contains any of these substrings, it
        is not doctested at all. This is similar to the ``# doctest +SKIP``
        directive. Typical candidates for this list are pseudocode blocks
        ``>>> from example import some_function`` or some such.
    skiplist : set
        A list of names of objects whose docstrings are known to fail doctesting
        and we like to keep it that way.
    user_context_mgr
        A context manager to run tests in. Is entered for each DocTest
        (for API docs, this is typically a single docstring). The operation is
        roughly

        >>> for test in tests:
        ...     with user_context(test):
        ...         runner.run(test)
        Default is a noop.
    local_resources: dict
        If a test needs some local files, list them here. The format is
        ``{test.name : list-of-files}``
        File paths are relative to path of ``test.filename``.
    parse_namedtuples : bool
        Whether to compare e.g. ``TTestResult(pvalue=0.9, statistic=42)``
        literally or extract the numbers and compare the tuple ``(0.9, 42)``.
        Default is True.
    nameerror_after_exception : bool
        If an example fails, next examples in the same test may raise spurious
        NameErrors. Set to True if you want to see these, or if your test
        is actually expected to raise NameErrors.
        Default is False.
    pytest_extra_ignore : list
        A list of names/modules to ignore when run under pytest plugin. This is
        equivalent to using `--ignore=...` cmdline switch.
    pytest_extra_skip : dict
        Names/modules to skip when run under pytest plugin. This is
        equivalent to decorating the doctest with `@pytest.mark.skip` or adding
        `# doctest: + SKIP` to its examples.
        Each key is a doctest name to skip, and the corresponding value is
        a string. If not empty, the string value is used as the skip reason.
    pytest_extra_xfail : dict
        Names/modules to xfail when run under pytest plugin. This is
        equivalent to decorating the doctest with `@pytest.mark.xfail` or
        adding `# may vary` to the outputs of all examples.
        Each key is a doctest name to skip, and the corresponding value is
        a string. If not empty, the string value is used as the skip reason.
    CheckerKlass : object, optional
        The class for the Checker object. Must mimic the ``DTChecker`` API:
        subclass the `doctest.OutputChecker` and make the constructor signature
        read ``__init__(self, config=None)``, where `config` is a ``DTConfig``
        instance.
        This class will be instantiated by ``DTRunner``.
        Defaults to `DTChecker`.
    ParserKlass : object, optional
        The class for the Parser object. Must mimic the ``DTParser`` API:
        subclass the `doctest.DocTestParser` and make the constructor signature
        be ``__init__(self, config=None)``, where ``config`` is a ``DTConfig``
        instance.
        This class will be instantiated by ``DTRunner`` via ``DTFinder``.
        Defaults to ``DTParser``.

    """
    def __init__(self, *, # DTChecker configuration
                          default_namespace=None,
                          check_namespace=None,
                          rndm_markers=None,
                          atol=1e-8,
                          rtol=1e-2,
                          strict_check=False,
                          # DTRunner configuration
                          optionflags=None,
                          # DTFinder/DTParser configuration
                          stopwords=None,
                          pseudocode=None,
                          skiplist=None,
                          # Additional user configuration
                          user_context_mgr=None,
                          local_resources=None,
                          # Obscure switches
                          parse_namedtuples=True,  # Checker
                          nameerror_after_exception=False,  # Runner
                          # plugin
                          pytest_extra_ignore=None,
                          pytest_extra_skip=None,
                          pytest_extra_xfail=None,
                          # plug-and-play configuration
                          CheckerKlass=None,
                          ParserKlass=None,
    ):
        ### DTChecker configuration ###

        # The namespace to run examples in
        self.default_namespace = default_namespace or {}

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
                  'int32': np.int32,
                  'uint32': np.uint32,
                  'int16': np.int16,
                  'uint16': np.uint16,
                  'int8': np.int8,
                  'uint8': np.uint8,
                  'float32': np.float32,
                  'float64': np.float64,
                  'dtype': np.dtype,
                  'nan': np.nan,
                  'nanj': np.complex128(1j*np.nan),
                  'infj': complex(0, np.inf),
                  'NaN': np.nan,
                  'inf': np.inf,
                  'Inf': np.inf, }
            self.check_namespace = check_namespace

        # Additional directives which act like `# doctest: + SKIP`
        if rndm_markers is None:
            rndm_markers = {'# random', '# Random',
                            '#random', '#Random',
                            "# may vary"}
        self.rndm_markers = rndm_markers
        self.atol, self.rtol = atol, rtol
        self.strict_check = strict_check

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
                 '.set(xlim=', '.set(ylim=', '.set(xlabel=', '.set(ylabel=', '.xlim(',
                 'ax.set(', '.text(',
            }
        self.stopwords = stopwords

        if pseudocode is None:
            pseudocode = set()
        self.pseudocode = pseudocode

        # these names are known to fail doctesting and we like to keep it that way
        # e.g. sometimes pseudocode is acceptable etc
        if skiplist is None:
            skiplist = set(['scipy.special.sinc',  # comes from numpy
                            'scipy.misc.who',  # comes from numpy
                            'scipy.optimize.show_options', ])
        self.skiplist = skiplist

        #### User configuration
        if user_context_mgr is None:
            user_context_mgr = util.noop_context_mgr
        self.user_context_mgr = user_context_mgr

        #### Local resources: None or dict {test: list-of-files-to-copy}
        self.local_resources=local_resources or dict()

        #### Obscure switches, best leave intact
        self.parse_namedtuples = parse_namedtuples
        self.nameerror_after_exception = nameerror_after_exception

        #### pytest plugin additional switches
        self.pytest_extra_ignore = pytest_extra_ignore or []
        self.pytest_extra_skip = pytest_extra_skip or {}
        self.pytest_extra_xfail = pytest_extra_xfail or {}

        ### Plug-and-play: Checker/Parser classes
        self.CheckerKlass = CheckerKlass or DTChecker
        self.ParserKlass = ParserKlass or DTParser


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


def try_convert_printed_array(got):
    """Printed arrays: reinsert commas.
    """
    # a minimal version is `s_got = ", ".join(got[1:-1].split())`
    # but it fails if there's a space after the opening bracket: "[ 0 1 2 ]"
    # For 2D arrays, split into rows, drop spurious entries, then reassemble.
    if not got.startswith('['):
        return got

    g1 = got[1:-1]  # strip outer "[...]"-s
    rows = [x for x in g1.split("[") if x]
    rows2 = [", ".join(row.split()) for row in rows]

    if got.startswith("[["):
        # was a 2D array, restore the opening brackets in rows; XXX clean up
        rows3 = ["[" + row for row in rows2]
    else:
        rows3 = rows2

    # add back the outer brackets
    s_got = "[" + ", ".join(rows3) + "]"
    return s_got


def has_masked(got):
    return 'masked_array' in got and '--' in got


def try_split_shape_from_abbrv(s_got):
    """NumPy 2.2 added shape=(123,) to abbreviated array repr.

    If present, split it off, and return a tuple. `(array, shape)`
    """
    if "shape=" in s_got:
        # handle
        # array(..., shape=(1000,))
        # array(..., shape=(100, 100))
        # array(..., shape=(100, 100), dtype=uint16)
        match = re.match(r'(.+),\s+shape=\(([\d\s,]+)\)(.+)', s_got, flags=re.DOTALL)
        if match:
            grp = match.groups()

            s_got = grp[0] + grp[-1]
            s_got = s_got.replace(',,', ',')
            shape_str = f'({grp[1]})'

            return ''.join(s_got.split('...,')), shape_str

    return ''.join(s_got.split('...,')), ''


class DTChecker(doctest.OutputChecker):
    obj_pattern = re.compile(r'at 0x[0-9a-fA-F]+>')
    vanilla = doctest.OutputChecker()

    def __init__(self, config=None):
        if config is None:
            config = DTConfig()
        self.config = config

        self.atol, self.rtol = self.config.atol, self.config.rtol
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
        ns = dict(self.config.check_namespace)
        try:
            a_want = eval(want, dict(ns))
            a_got = eval(got, dict(ns))
        except Exception:
            # Maybe we're printing a numpy array? This produces invalid python
            # code: `print(np.arange(3))` produces "[0 1 2]" w/o commas between
            # values. So, reinsert commas and retry.
            s_want = want.strip()
            s_got = got.strip()
            cond = (s_want.startswith("[") and s_want.endswith("]") and
                    s_got.startswith("[") and s_got.endswith("]"))
            if cond:
                s_want = try_convert_printed_array(s_want)
                s_got = try_convert_printed_array(s_got)

                return self.check_output(s_want, s_got, optionflags)
            
            #handle array abbreviation for n-dimensional arrays, n >= 1
            ndim_array = (s_want.startswith("array([") and "..." in s_want and 
                          s_got.startswith("array([") and "..." in s_got)
            if ndim_array:
                s_want, want_shape = try_split_shape_from_abbrv(s_want)
                s_got, got_shape = try_split_shape_from_abbrv(s_got)

                if got_shape:
                    # NumPy 2.2 output, `with shape=`, check the shapes, too
                    s_want = f"{s_want}, {want_shape}"
                    s_got = f"{s_got}, {got_shape}"

                return self.check_output(s_want, s_got, optionflags)

            # maybe we are dealing with masked arrays?
            # their repr uses '--' for masked values and this is invalid syntax
            # If so, replace '--' by nans (they are masked anyway) and retry
            if has_masked(want) or has_masked(got):
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

            if not self.config.parse_namedtuples:
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

        # Validate data type if list or tuple
        is_list_or_tuple = (isinstance(a_want, (list, tuple)) and
                            isinstance(a_got, (list, tuple)))
        if is_list_or_tuple and type(a_want) is not type(a_got):
            return False

        # ... and defer to numpy
        strict = self.config.strict_check
        try:
            return self._do_check(a_want, a_got, strict)
        except Exception:
            # heterog tuple, eg (1, np.array([1., 2.]))
            try:
                return all(
                    self._do_check(w, g, strict) for w, g in zip_longest(a_want, a_got)
                )
            except (TypeError, ValueError):
                return False

    def _do_check(self, want, got, strict_check):
        # This should be done exactly as written to correctly handle all of
        # numpy-comparable objects, strings, and heterogeneous tuples

        # NB: 3 == np.float64(3.0) but dtypes differ
        if strict_check:
            want_dtype = np.asarray(want).dtype
            got_dtype = np.asarray(got).dtype
            if want_dtype != got_dtype:
                return False

        try:
            if want == got:
                return True
        except Exception:
            pass

        # This line is the crux of the whole thing. The rest is mostly scaffolding.
        result = np.allclose(want, got, atol=self.atol, rtol=self.rtol, equal_nan=True)
        return result


class DTRunner(doctest.DocTestRunner):
    DIVIDER = "\n"

    def __init__(self, checker=None, verbose=None, optionflags=None, config=None):
        if config is None:
            config = DTConfig()
        if checker is None:
            checker = config.CheckerKlass(config)
        self.nameerror_after_exception = config.nameerror_after_exception
        if optionflags is None:
            optionflags = config.optionflags
        super().__init__(checker=checker, verbose=verbose, optionflags=optionflags)

    def _report_item_name(self, out, item_name, new_line=False):
        if item_name is not None:
            out("\n " + item_name + "\n " + "-"*len(item_name))
            if new_line:
                out("\n")

    def report_start(self, out, test, example):
        return super().report_start(out, test, example)

    def report_success(self, out, test, example, got):
        if self._verbose:
            self._report_item_name(out, test.name, new_line=True)
        return super().report_success(out, test, example, got)

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
        return super().report_failure(out, test, example, got)

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
        r = super().run(
            test, compileflags=compileflags, out=out, clear_globs=clear_globs
        )
        if clear_globs:
            test.globs.clear()
        return r

    def report_unexpected_exception(self, out, test, example, exc_info):
        super().report_unexpected_exception(out, test, example, exc_info)
        out('\n')
        raise doctest.UnexpectedException(test, example, exc_info)

    def report_failure(self, out, test, example, got):
        super().report_failure(out, test, example, got)
        out('\n')
        raise doctest.DocTestFailure(test, example, got)


class DTFinder(doctest.DocTestFinder):
    """A Finder with helpful defaults.
    """
    def __init__(self, verbose=None, parser=None, recurse=True,
                 exclude_empty=True, config=None):
        if config is None:
            config = DTConfig()
        self.config = config
        if parser is None:
            parser = config.ParserKlass(config)
        verbose, dtverbose = util._map_verbosity(verbose)
        super().__init__(dtverbose, parser, recurse, exclude_empty)

    def find(self, obj, name=None, module=None, globs=None, extraglobs=None):
        if globs is None:
            globs = dict(self.config.default_namespace)
        # XXX: does this make similar checks in testmod/testfile duplicate?
        if module not in self.config.skiplist:   
            tests = super().find(obj, name, module, globs, extraglobs)

            if inspect.isclass(obj):
                for name_, method in inspect.getmembers(obj):
                    if inspect.isdatadescriptor(method):
                        tests += super().find(
                            method, f'{name}.{name_}', module, globs, extraglobs
                        )
            return tests


class DTParser(doctest.DocTestParser):
    """A Parser with a stopword list.
    """
    def __init__(self, config=None):
        if config is None:
            config = DTConfig()
        self.config = config
        # DocTestParser has no __init__, do not try calling it

    def get_examples(self, string, name='<string>'):
        """Get examples from intervening strings and examples.

        How this works
        --------------
        This function is used (read the source!) in
        `doctest.DocTestParser().get_doctests(...)`. Over there, `self.parse`
        splits the input string into into a list of `Examples` and intervening
        text strings. `get_examples` method selects `Example`s from this list.
        Here we inject our logic for filtering out stopwords and pseudocode.

        TODO: document the differences between stopwords, pseudocode and +SKIP.
        """
        stopwords = self.config.stopwords
        pseudocode = self.config.pseudocode
        rndm_markers = self.config.rndm_markers

        SKIP = doctest.OPTIONFLAGS_BY_NAME['SKIP']
        keep_skipping_this_block = False

        examples = []
        for example in self.parse(string, name):
            # .parse returns a list of examples and intervening text
            if not isinstance(example, doctest.Example):
                if example:
                    keep_skipping_this_block = False
                continue

            if SKIPBLOCK in example.options or keep_skipping_this_block:
                # skip this one and continue skipping until there is
                # a non-empty line of text (which signals the end of the block)
                example.options[SKIP] = True
                keep_skipping_this_block = True

            if any(word in example.source for word in pseudocode):
                # Found pseudocode. Add a `#doctest: +SKIP` directive.
                # NB: Could have just skipped it via `continue`.
                example.options[SKIP] = True

            if any(word in example.source for word in rndm_markers):
                # Found a `# may vary`. Do not check the output (but do check
                # that the source is valid python).
                example.want += "  # _ignore\n"

            if any(word in example.source for word in stopwords):
                # Found a stopword. Do not check the output (but do check
                # that the source is valid python).
                example.want += "  # _ignore\n"
            examples.append(example)
        return examples

