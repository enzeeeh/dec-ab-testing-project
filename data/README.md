# Public Dataset for A/B Testing

This folder contains sample datasets for A/B testing. Below is a description of the included dataset:

## Dataset: `test1_menu.csv`
- **Description**: Simulated data for testing the impact of menu design on conversion rates.
- **Columns**:
  - `user_id`: Unique identifier for each user.
  - `variant`: The variant assigned to the user (e.g., `A` or `B`).
  - `conversion_rate`: Binary metric indicating whether the user converted (1) or not (0).

## Public Dataset Source
For additional practice, you can use the following public dataset:
- **Name**: Kaggle's "AB Testing Dataset"
- **URL**: [https://www.kaggle.com/datasets/](https://www.kaggle.com/datasets/)

To use the public dataset, download it and place it in this folder. Update the `data_path` in `run_pipeline.py` to point to the new dataset.