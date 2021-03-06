import numpy as np
import pandas as pd
import h5py as h5

import os
import os.path as op


def main(sas_output_path, py_output_dir, rerun=False):
    '''If this module is run directly it calculates per variable difference
    between the SAS output read from sas_output_path and Python output
    read from CSV files contained in py_output_dir.

    If the arg "rerun" is anything but False, taxcalc gets imported and its Test
    function run, thus regenerating the python output.
    '''
    if rerun:
        cwd = os.getcwd()
        import translation
        os.chdir(python_output_dir)
        translation.Test(True)
        os.chdir(cwd)
    
    gold_std = h5.File(sas_codes_path)
    errors = compute_error(gen_file_paths(py_output_dir), gold_std)
    errors.columns = ['Error']
    errors.sort(columns='Error', ascending=False, inplace=True)
    errors.to_csv('errors_by_variable.csv',
        index_label='Variable'
        )


def compute_error(files_to_look_at, gold_std):
    '''Computes the "error" by looping through CSV files in "files_to_look_at"
    and comparing the values of c-code variables generated by Python to
    corresponding values from the gold_std (data generated by SAS).
    '''
    error = {}
    for file_name in files_to_look_at:
        file_vars = pd.read_csv(file_name)
        for var_name in file_vars:
            is_c_code = var_name.lower().startswith('c')
            if is_c_code and var_name not in error:
                per_taxpayer_diff = file_vars[var_name] - gold_std[var_name]
                error[var_name] = np.absolute(per_taxpayer_diff).sum()

    return pd.DataFrame.from_dict(error, orient='index')


def mismatching_records(gold_std, variable, py_out_dir='py_output'):
    '''
    Given gold_std as a mapping of variable names to their values according to
    SAS and the name of one particular variable as well as a folder containing
    the CSVs produced by our Python script attempts to create a list of
    indeces (which represent taxpayer records) where SAS values for variable
    do not match its Python values.
    '''
    # first we need to find the python values for this variable
    py_answer = None
    for file_path in gen_file_paths(py_out_dir):
        temp = pd.read_csv(file_path)
        if variable in temp:
            print 'Found in file: {}'.format(file_path)
            py_answer = temp[variable]
            break
    
    if not py_answer:
        print 'Variable was not found, returning None. Beware!'
        return py_answer
    
    mismatches = np.array(np.absolute(py_answer - gold_std[variable]) > 0)

    if not mismatches.any():
        print 'No cells satisfied the condition, returning series as is'
        return mismatches

    all_indices = np.arange(len(mismatches))
    return all_indices[mismatches]


def report_accuracy(sas_codes, indx, python_output_dir='py_output'):
    '''Generates a csv for one taxpayer specified by indx.
    This csv contains variable names as row labels and corresponding SAS output
    compared with Python output.
    '''
    value_comparison = {}
    for var_file_path in gen_file_paths(python_output_dir):
        python_variables_df = pd.read_csv(var_file_path)
        # select all records in index row and update accuracy dict
        value_comparison.update(python_variables_df.iloc[indx].to_dict())

    value_comparison = merge_dicts(sas_codes, indx, value_comparison)
    value_comp_df = pd.DataFrame.from_dict(value_comparison, orient='index')
    value_comp_df.to_csv('accuracy.csv')


def gen_file_paths(dir_name, filter_func=None):
    '''A function for wrapping all the os.path commands involved in listing files
    in a directory, then turning file names into file paths by concatenating
    them with the directory name.
    
    This also optionally supports filtering file names using filter_func.

    :param dir_name: name of directory to list files in
    :type dir_name: string
    :param filter_func: optional name of function to filter file names by
    :type filter_func: None by default, function if passed
    :returns: sequence of paths for files in *dir_name*
    '''
    file_paths = tuple(op.join(dir_name, file_name) 
        for file_name in os.listdir(dir_name))
    if filter_func:
        return filter(filter_func, file_paths)    
    return file_paths


def merge_dicts(sas_codes, taxpayer, python_codes):
    '''
    Combines SAS output for a taxpayer with the corresponding python output.
    '''
    result = {}
    for variable in sas_codes:
        sas_taxpayer = sas_codes[variable][taxpayer]
        # occasionally Python's versions of the variable name are lowercase
        lc_v = variable.lower()
        if variable in python_codes:
            result[variable] = (sas_taxpayer, python_codes[variable])
        elif lc_v in python_codes:
            result[lc_v] = (sas_taxpayer, python_codes[lc_v])
        else:
            result[variable] = (sas_taxpayer, '')
    return result


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser('Testing script')
    parser.add_argument('sas_codes_path',
        help='path to HDF5 file with SAS codes')
    parser.add_argument('py_out_dir',
        help='path to folder with Python-generated values')
    parser.add_argument('-r', dest='rerun', action='store_true',
        help=('pass this flag to regenerate Python data'))

    cmd_input = parser.parse_args()
    main(cmd_input.sas_codes_path, cmd_input.py_output_dir, cmd_input.rerun)
