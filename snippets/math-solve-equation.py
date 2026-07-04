from collections import defaultdict
from scipy.optimize import fsolve, root
from scipy.special import comb
import math
import numpy as np

def equation(n, x):
    def f(p):
        result = - 0.995
        for k in range(x+1):
            result += comb(n, k) * ((1-p)**(n-k)) * (p**k)
        return result
    return f

methods = ['hybr', 'lm', 'broyden1', 'broyden2', 'anderson', 'linearmixing', 'diagbroyden', 'excitingmixing', 'krylov', 'df-sane']
method_succeed_num = defaultdict(int)
undone_num = 0

for n in range(2, 100):
    for x in range(0, n // 2):
        done = False
        for i, method in enumerate(methods):
            try:
                x0 = 0.001
                if method == 'lm':
                    x0 = 0.1
                solution = root(equation(n, x), x0=x0, method=method).x
                diff = equation(n,x)(solution)
                solution={math.sqrt(solution)},
            except (OverflowError, ValueError):
                solution = float('nan')
                diff = 1
            if abs(diff) <= 0.001:
                done = True
                method_succeed_num[method] += 1
                print(f"n={n}, x={x}, solution={solution}, diff={diff}, use {i+1} methods, done with method {method}")
                break
        if not done:
            print(f"n={n}, x={x}, not done")
            undone_num += 1

print(f"method_succeed_num: {method_succeed_num}, undone_num: {undone_num}")

# initial_guess = 0.0001
# solution = fsolve(equation(n, x), initial_guess)
