import numpy as np

def remove_extreme_values_with_median(data: np.ndarray):
    # data is the factor exposure on all stocks at the T'th bar
    # data's shape is (n_stocks, 1)
    median_value = np.median(data)
    abs_data_minus_median = np.abs(data - median_value)
    median_value_of_abs_data_minus_median = np.median(abs_data_minus_median)
    max_available_value = median_value + 5 * median_value_of_abs_data_minus_median
    min_available_value = median_value - 5 * median_value_of_abs_data_minus_median
    data[data > max_available_value] = max_available_value
    data[data < min_available_value] = min_available_value
    return data

def remove_extreme_values_with_3sigma(data: np.ndarray):
    mean_value = np.mean(data)
    std_value = np.std(data)
    data[data > mean_value + 3 * std_value] = mean_value + 3 * std_value
    data[data < mean_value - 3 * std_value] = mean_value - 3 * std_value
    return data

def normalize_factor_exposure(data: np.ndarray):
    # data is the factor exposure on all stocks at the T'th bar
    # data's shape is (n_stocks, 1)
    mean_value = np.mean(data)
    std_value = np.std(data)
    data = (data - mean_value) / std_value
    return data

def preprocess_factor_exposure(data: np.ndarray, remove_method: str = "median"):
    # data is the factor exposure on all stocks at the T'th bar
    # data's shape is (n_stocks, 1)
    if remove_method == "median":
        data = remove_extreme_values_with_median(data)
    elif remove_method == "3sigma":
        data = remove_extreme_values_with_3sigma(data)
    data = normalize_factor_exposure(data)
    return data
