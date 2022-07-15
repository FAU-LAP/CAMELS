import numpy as np
from bluesky import plan_stubs as bps


def get_fit_results(fits, namespace, add_flat=False):
    if 'fits' not in namespace:
        namespace['fits'] = {}
    for name, fit in fits.items():
        if not fit.result:
            continue
        entry = name
        i = 0
        while entry in namespace['fits']:
            entry = f'{entry}_{i}'
        namespace['fits'][entry] = {}
        namespace['fits'][entry]['result'] = fit.result.best_values
        namespace['fits'][entry]['covariance'] = fit.result.covar
        if add_flat:
            for k, v in fit.result.best_values:
                flatname = f'{name}:{k}'
                namespace[flatname] = v
    # TODO yield from read for fits!


def gradient_descent(max_iterations, threshold, w_init, func_text, evaluator,
                     set_channel, read_channels, min_step, max_step, min_val,
                     max_val, stream_name='gradient_descent', learning_rate=0.05,
                     momentum=0.8, max_step_for_diff=None):

    def obj_func(set_val):
        yield from bps.checkpoint()
        yield from bps.abs_set(set_channel, set_val, group='A')
        yield from bps.wait('A')
        yield from bps.trigger_and_read(read_channels, name=stream_name)
        # yield from bps.sleep(1)

    if max_step_for_diff is None:
        max_step_for_diff = 10 * min_step

    w = w_init
    w_history = [w]
    yield from obj_func(w)
    f_history = [evaluator.eval(func_text)]
    if w - min_val > max_val - w:
        w -= max_step_for_diff
        delta_w = -max_step_for_diff
    else:
        w += max_step_for_diff
        delta_w = max_step_for_diff
    i = 0
    diff = np.inf

    while i < max_iterations and (diff > threshold or np.abs(delta_w) > max_step_for_diff):
        yield from obj_func(w)
        f = evaluator.eval(func_text)
        grad = (f - f_history[-1]) / (w - w_history[-1])
        delta_w = -learning_rate * grad + momentum * delta_w
        w_history.append(w)
        f_history.append(f)
        if np.abs(delta_w) > max_step:
            delta_w = np.sign(delta_w) * max_step
        elif np.abs(delta_w) < min_step:
            delta_w = np.sign(delta_w) * min_step
        w += delta_w
        if w < min_val:
            w = min_val
        elif w > max_val:
            w = max_val
        if w == w_history[-1]:
            if w - min_val > max_val - w:
                w -= max_step_for_diff
                delta_w -= max_step_for_diff
            else:
                w += max_step_for_diff
                delta_w = max_step_for_diff
        # store the history of w and f

        # update iteration number and diff between successive values
        # of objective function
        i += 1
        diff = np.abs(f_history[-1]-f_history[-2])

    sort_w = [i for j, i in sorted(zip(f_history, w_history))]
    sort_f = sorted(f_history)
    while True:
        fs = []
        for i in range(2):
            yield from obj_func(sort_w[0])
            fs.append(evaluator.eval(func_text))
        if fs[0] and fs[1] < sort_f[0] + 0.1 * (sort_f[-1] - sort_f[0]):
            break
        elif len(sort_f) < 0.5 * len(f_history):
            yield from obj_func(w_init)
            break
        else:
            sort_f.pop(0)
            sort_w.pop(0)
    return w_history,f_history
