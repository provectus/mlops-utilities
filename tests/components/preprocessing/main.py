import logging
import tarfile
from pathlib import Path
import json

import numpy as np
import pandas as pd
from joblib import dump, load
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DEFAULT_DATA_FILE_NAME = "data.csv"
DEFAULT_HEADER_FILE_NAME = "header.json"
FEATURIZER_FILE_NAME = "column_transformer.model"

ID_COLUMN = "ID"
LABEL_COLUMN = "rings"

# Since we get a headerless CSV file we specify the column names here.
DATA_COLUMN_NAMES = [
    ID_COLUMN,
    "sex",
    "length",
    "diameter",
    "height",
    "whole_weight",
    "shucked_weight",
    "viscera_weight",
    "shell_weight",
]

LABEL_COLUMN_NAMES = [
    ID_COLUMN,
    LABEL_COLUMN
]

DATA_COLUMN_DTYPES = {
    ID_COLUMN : np.int64,
    "sex": str,
    "length": np.float64,
    "diameter": np.float64,
    "height": np.float64,
    "whole_weight": np.float64,
    "shucked_weight": np.float64,
    "viscera_weight": np.float64,
    "shell_weight": np.float64,
}

LABEL_COLUMN_DTYPES = {
    ID_COLUMN : np.int64,
    LABEL_COLUMN: np.float64
}


# call with header=0 if there is a header row
def read_data_csv(fn, header=None):
    return pd.read_csv(
        Path(fn, DEFAULT_DATA_FILE_NAME),
        header=header,
        names=DATA_COLUMN_NAMES,
        dtype=DATA_COLUMN_DTYPES,
        index_col=ID_COLUMN,
    )


def read_label_csv(fn, header=None):
    return pd.read_csv(
        Path(fn, DEFAULT_DATA_FILE_NAME),
        header=header,
        names=LABEL_COLUMN_NAMES,
        dtype=LABEL_COLUMN_DTYPES,
        index_col=ID_COLUMN,
    )


def save_to_csv(df, output_path, header=False, index=True):
    logger = logging.getLogger(__name__)
    output_path = Path(output_path)
    output_path.mkdir(exist_ok=True, parents=True)
    logger.info("Writing to %s", output_path / DEFAULT_DATA_FILE_NAME)
    df.to_csv(output_path / DEFAULT_DATA_FILE_NAME, header=header, index=index)


def save_for_xgboost(df, output_path):
    output_path = Path(output_path)
    output_path.mkdir(exist_ok=True, parents=True)
    path = output_path / DEFAULT_DATA_FILE_NAME
    df.to_csv(path, header=False, index=False)
    with (output_path / DEFAULT_HEADER_FILE_NAME).open(mode='w') as out:
        json.dump(
            {
                "header" : df.columns.to_list()
            },
            out
        )


FORMAT_CSV_FULL = lambda df, output_path: save_to_csv(df, output_path, header=True, index=True)
FORMAT_CSV_XGBOOST = lambda df, output_path: save_for_xgboost(df, output_path)
FORMAT_CSV_DATAQA = lambda df, output_path: save_to_csv(df, output_path, header=True, index=False)


def step_split(
    input_data_path,
    input_label_path,
    output_train_dataset_data,
    output_train_dataset_labels,
    output_test_dataset_data,
    output_test_dataset_labels,
    train_part=0.8,
):
    data_df = read_data_csv(input_data_path, header=0)
    label_df = read_label_csv(input_label_path, header=0)
    train_data_df, train_label_df, test_data_df, test_label_df = split_dataset(
        data_df, label_df, train_part
    )
    save_to_csv(train_data_df, output_train_dataset_data)
    save_to_csv(train_label_df, output_train_dataset_labels)
    save_to_csv(test_data_df, output_test_dataset_data)
    save_to_csv(test_label_df, output_test_dataset_labels)


def split_dataset(
    data_df: pd.DataFrame, label_df: pd.DataFrame, train_part=0.8
):
    (
        train_data_df,
        test_data_df,
        train_label_df,
        test_label_df,
    ) = train_test_split(
        data_df, label_df, test_size=1 - train_part, shuffle=True
    )
    return train_data_df, train_label_df, test_data_df, test_label_df


# monkey patching Imputers and Scalers, fixed in Scikit-Learn 1.1 but we can't upgrade to this because
# there is requirement in python 3.8 which does not hold for SageMaker Scikit-Learn prebuilt images
def _get_feature_names_out(self, input_feature_names):
    return input_feature_names


SimpleImputer.get_feature_names_out = _get_feature_names_out
StandardScaler.get_feature_names_out = _get_feature_names_out


def fit_featurizers(input_data_path, output_path):
    logger = logging.getLogger(__name__)
    logger.info("Reading from %s", input_data_path)
    df = read_data_csv(input_data_path)

    logger.info("Fitting transforms.")
    numeric_features = list(df.columns)
    numeric_features.remove("sex")
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_features = ["sex"]
    categorical_transformer = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="constant", fill_value="missing"),
            ),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocess = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )
    preprocess.fit(df)
    logger.info("sklearn version %s", sklearn.__version__)
    logger.info("get_feature_names_out...", preprocess.get_feature_names_out())
    output_path = Path(output_path)
    output_path.mkdir(exist_ok=True, parents=True)
    output_file = output_path / FEATURIZER_FILE_NAME
    logger.info("Saving to %s...", output_file)
    dump(preprocess, output_file)
    logger.info("Done.")


def step_featurize(input_data_path, transformer_path, output_data_path):
    logger = logging.getLogger(__name__)
    logger.info("Reading from %s", input_data_path)
    input_df = read_data_csv(input_data_path)
    logger.info("Loading from %s", transformer_path)
    preprocess: ColumnTransformer = load(Path(transformer_path, FEATURIZER_FILE_NAME))
    logger.info("Applying transform to get features")
    _feature_df_data = apply_featurizers(input_df, preprocess)
    logger.info(type(preprocess))
    _feature_df_columns = preprocess.get_feature_names_out()
    feature_df = pd.DataFrame(_feature_df_data, columns=_feature_df_columns, index=input_df.index)
    save_to_csv(feature_df, output_data_path, header=True)
    logger.info("Done.")


def step_apply(
    serialized_featurizers,
    train_dataset_data,
    test_dataset_data,
    train_dataset_features,
    test_dataset_features,
):
    step_featurize(
        train_dataset_data, serialized_featurizers, train_dataset_features
    )
    step_featurize(
        test_dataset_data, serialized_featurizers, test_dataset_features
    )


def apply_featurizers(input_df, preprocess) -> pd.DataFrame:
    return preprocess.transform(input_df)


def merge(input_features_path, input_labels_path, output_path, output_format):
    data_df = pd.read_csv(
        Path(input_features_path, DEFAULT_DATA_FILE_NAME),
        header=0,
        index_col=ID_COLUMN,
    )
    label_df = read_label_csv(input_labels_path)
    merged_df = pd.concat([label_df, data_df], axis=1)
    output_format(merged_df, output_path)


def step_merge(
    train_data, train_labels, test_data, test_labels, data_output, test_output
):
    merge(train_data, train_labels, data_output, FORMAT_CSV_XGBOOST)
    merge(test_data, test_labels, test_output, FORMAT_CSV_XGBOOST)


def step_prepare_baseline_dataset(input_data_path, output_path):
    data_df = read_data_csv(input_data_path)
    data_df = data_df.reset_index(drop=True)

    FORMAT_CSV_DATAQA(data_df, output_path)


def make_archive(input_path: str, output_path: str):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    with tarfile.open(output_path, mode="w:gz") as tar:
        # if "input_path" is a folder, then we add its content to an archive, not the folder itself
        in_archive_name = input_path.name if input_path.is_file() else ""
        tar.add(input_path, arcname=in_archive_name)


if __name__ == "__main__":
    import fire

    logging.basicConfig(level=logging.INFO)
    fire.Fire(
        {
            "split": step_split,
        }
    )
