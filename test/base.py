"""
Many useful functions for testing and debugging. `Check` is the main function you should use because it will do everything for you.

It is helpful to make your own functions that call `Check` with the correct arguments, so you can easily test your code.

e.g.
```python
def testPoint(testName, outs, expected1, expected2, ins):
    Check(testName,
        ['x', 'y', 'accelx', 'accely'],
        ins,
        [outs[0][0], outs[0][1], outs[1][0], outs[1][1]],
        [*expected1, *expected2],
        lambda li: f'({li[0]}, {li[1]}), [{li[2]}, {li[3]}]'
    )

testPoint('Perfect rebound',
        collisions.Point(2, 0).handleCollisionsVel([0, 2], collisions.Shapes(collisions.Rect(0, 1, 4, 4, 1))),
        (2, 0), # It rebounded perfectly and now is exactly where it started
        (0, -2), # It is now going the opposite direction
        (2, 0, 0, 2))
```

For more examples, see `BlazeSudio/test/tests.py`.
"""
from typing import Any, Callable
import time

__all__ = [
    'Check',
    'CheckFunc',
    'CompareTimes',

    'DebugTable',
    'Timeit',

    'RoundAny',
]

SupportedFormats = int|float
SupportedTypes = SupportedFormats|tuple[SupportedFormats]|list[SupportedFormats]

DEFAULT_FORMATTER = lambda li: ' '.join(li)

def DebugTable(names: list[str],
               formatter: Callable[[list[Any]], str] = DEFAULT_FORMATTER,
               highlights: list[int] = None,
               **rows: dict[str, tuple[SupportedTypes]]
          ) -> None:
    """
    Print a debug table with the given inputs and outputs.

    Args:
        names (list[str]): The names of the inputs.
        formatter (Callable[[tuple[SupportedTypes]], str], optional): A function that takes a list of inputs and returns a string. (e.g. `lambda li: f'({li[0]}, {li[1]})'`). Defaults to `lambda li: ' '.join(li)`.
        highlights (list[int], optional): Which list elements to highlight. Defaults to None.
        **rows (dict[str, tuple[SupportedTypes]]): A dictionary of `str: tuple[SupportedTypes]` values. These will be the rows in the table, and each value will be converted to strings.

    Raises:
        ValueError: If the `rows` argument is of incorrect format.
    """
    if not all(isinstance(i, str) for i in rows.keys()):
        raise ValueError(
            'Not all rows keys are strings!'
        )
    if not all(hasattr(i, '__iter__') for i in rows.values()):
        raise ValueError(
            'Not all rows are iterable!'
        )
    rows = {i: tuple(str(j) for j in rows[i]) for i in rows}
    fstValLen = len(tuple(rows.values())[0])
    if any(len(i) != fstValLen for i in rows.values()):
        raise ValueError(
            'All rows must be the same length.'
        )

    def adjust(t, ln):
        return t + ' ' * (ln - len(t))
        # return ' ' * ((ln - len(t)) // 2) + t + ' ' * ((ln - len(t) + 1) // 2)

    ls = [names] + list(rows.values())
    max_lens = [max(len(j[i]) for j in ls) for i in range(fstValLen)]
    spacing = max(len(i) for i in rows.keys())

    print(' '*(spacing+2) + formatter(names))
    for nme, vals in rows.items():
        nvals = [adjust(vals[i], max_lens[i]) for i in range(len(vals))]
        print(nme+': '+' '*(spacing-len(nme)) + formatter(nvals))

    if highlights is not None:
        fmt = formatter(tuple(
            ('^' if i in highlights else ' ')*max_lens[i] for i in range(fstValLen)
        ))
        for let in set(fmt):
            if let not in ' ^':
                fmt = fmt.replace(let, ' ')
        print(' ' * (spacing+2) + fmt)
    else:
        print()

def RoundAny(t: SupportedTypes) -> SupportedTypes:
    """
    Round a number or a list of numbers to 2 decimal places.
    """
    if isinstance(t, (tuple, list)):
        return type(t)(RoundAny(x) for x in t)
    return round(t, 2)

def Check(testName: str,
          names: list[str],
          ins: list[SupportedTypes],
          outs: list[SupportedTypes],
          expecteds: list[SupportedTypes],
          formatter: Callable[[list[SupportedTypes]], str] = DEFAULT_FORMATTER
          ) -> None:
    """
    Check if the outputs are the same as the expected outputs, and if not raise an AssertionError and print a helpful DebugTable.

    Args:
        testName (str): The name of the test running.
        names (list[str]): The names of the inputs.
        ins (list[SupportedTypes]): The inputs to the func.
        outs (list[SupportedTypes]): The outputs from the func.
        expecteds (list[SupportedTypes]): The expected outputs from the func.
        formatter (Callable[[list[SupportedTypes]], str], optional): The function that formats the rows. Defaults to `lambda li: ' '.join(li)`.

    Raises:
        ValueError: If the lengths of the arguments (except formatter and testName) are not the same.
        AssertionError: If the inputs do not match the expected outputs (to 2 d.p).
    """
    if len(ins) != len(outs) or len(outs) != len(expecteds) or len(expecteds) != len(names):
        raise ValueError('All inputs must be the same length.')

    errors = []
    errortxts = []
    for i in range(len(ins)):
        if RoundAny(outs[i]) != expecteds[i]:
            errors.append(i)
            errortxts.append(f'In {names[i]}: expected {expecteds[i]}, got {outs[i]}')
    if errors != []:
        print(f'TEST {testName} FAILED:')
        DebugTable(
            names,
            formatter,
            errors,
            ins=ins,
            outs=outs,
            expecteds=expecteds
        )
        raise AssertionError(
            ' &\n'.join(errortxts)
        )

def AssertEqual(testName: str,
                names: list[str],
                outs1: list[SupportedTypes],
                outs2: list[SupportedTypes],
                formatter: Callable[[list[SupportedTypes]], str] = DEFAULT_FORMATTER
                ) -> None:
    """
    Check if the outputs are the same, and if not raise an AssertionError and print a helpful DebugTable.

    Args:
        testName (str): The name of the test running.
        names (list[str]): The names of the inputs.
        outs1 (list[SupportedTypes]): The first set of outputs.
        outs2 (list[SupportedTypes]): The second set of outputs.
        formatter (Callable[[list[SupportedTypes]], str], optional): The function that formats the rows. Defaults to `lambda li: ' '.join(li)`.

    Raises:
        ValueError: If the lengths of the arguments (except formatter and testName) are not the same.
        AssertionError: If the inputs do not match the expected outputs (to 2 d.p).
    """
    if len(outs1) != len(outs2) or len(outs2) != len(names):
        raise ValueError('All inputs must be the same length.')

    errors = []
    errortxts = []
    for i in range(len(outs1)):
        if RoundAny(outs1[i]) != RoundAny(outs2[i]):
            errors.append(i)
            errortxts.append(f'In {names[i]}: expected {outs2[i]}, got {outs1[i]}')
    if errors != []:
        print(f'TEST {testName} FAILED:')
        DebugTable(
            names,
            formatter,
            errors,
            out1=outs1,
            out2=outs2
        )
        raise AssertionError(
            ' &\n'.join(errortxts)
        )

# TODO: Average times
def Timeit(func: Callable, *args, **kwargs):
    """
    Time how long it takes to run a function.

    Args:
        func (Callable): The function to call.
        *args: The arguments to pass to the function.
        **kwargs: The keyword arguments to pass to the function.
    """
    start = time.time()
    func(*args, **kwargs)
    print(f'Time taken: {(time.time() - start)*1000} ms.')

def CompareTimes(testName: str, name1: str, func1: Callable, name2: str, func2: Callable, *args, **kwargs):
    """
    Compare the times taken for two functions to run.

    Args:
        testName (str): The name of the test running.
        name1: The name of the first function.
        func1: The first function.
        name2: The name of the second function.
        func2: The second function.
        *args: The arguments to pass to the functions.
        **kwargs: The keyword arguments to pass to the functions.
    """
    start = time.time()
    func1(*args, **kwargs)
    f1Time = time.time() - start
    start = time.time()
    func2(*args, **kwargs)
    f2Time = time.time() - start
    f1Time *= 1000
    f2Time *= 1000

    print('TEST', testName)
    print(f'Time taken for {name1.lower()}: {f1Time} ms, time taken for {name2.lower()}: {f2Time} ms.')
    print(f'Difference: {abs(f1Time - f2Time)} ms.')
    if f1Time == 0 or f2Time == 0:
        return
    if f1Time > f2Time:
        print(f'{name1[0].upper()+name1[1:].lower()} is {f2Time/f1Time} times faster (~{round(f2Time/f1Time*100, 3)}%) than {name2.lower()}.')
    else:
        print(f'{name2[0].upper()+name2[1:].lower()} is {f1Time/f2Time} times faster (~{round(f1Time/f2Time*100, 3)}%) than {name1.lower()}.')
