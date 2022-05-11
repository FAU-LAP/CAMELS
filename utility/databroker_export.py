import databroker
import h5py


def recourse_entry_dict(entry, metadata):
    for key, val in metadata.items():
        if isinstance(val, databroker.core.Start) or isinstance(val, databroker.core.Stop):
            val = dict(val)
        if type(val) is dict:
            sub_entry = entry.create_group(key)
            recourse_entry_dict(sub_entry, val)
        elif type(val) is list:
            for i, value in enumerate(val):
                if isinstance(value, dict):
                    sub_entry = entry.create_group(f'{key}_{i}')
                    recourse_entry_dict(sub_entry, value)
                else:
                    entry.attrs[f'{key}_{i}'] = val
        elif val is None:
            continue
        else:
            entry.attrs[key] = val

def broker_to_hdf5(runs, filename):
    if not isinstance(runs, list):
        runs = [runs]
    for run in runs:
        metadata = run.metadata
        with h5py.File(filename, 'a') as file:
            entry = file.create_group(run.name)
            recourse_entry_dict(entry, metadata)
            for stream in run:
                dataset = run[stream].read()
                group = entry.create_group(stream)
                for col in dataset:
                    group[col] = dataset[col]
                for coord in dataset.coords:
                    group[coord] = dataset[coord]

