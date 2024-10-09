import pandas as pd
import os
from datetime import datetime
import json

def save_training_data(df_results, confg):
    """
    Save training data (df_results and confg) into separate directories
    for model training.

    Parameters:
    - df_results (pd.DataFrame): DataFrame containing the y values.
    - confg (dict): Dictionary containing 'physical_machines' and 
      'virtual_machines' configurations.
    """
    # Get current time
    current_time = datetime.now()
    timestamp = current_time.strftime("%Y_%m_%d_%H_%M")
    
    # Create main directory if not exists
    main_dir = ".\\training_data"
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)
    
    # Save df_results in 'y' subdirectory
    y_dir = os.path.join(main_dir, "y")
    if not os.path.exists(y_dir):
        os.makedirs(y_dir)
    df_results.to_csv(os.path.join(y_dir, f"y_{timestamp}.csv"), index=False)
    
    # Save confg in 'x' subdirectory
    x_dir = os.path.join(main_dir, "x")
    if not os.path.exists(x_dir):
        os.makedirs(x_dir)
    confg_dir = os.path.join(x_dir, f"x_{timestamp}")
    os.makedirs(confg_dir)
    with open(os.path.join(confg_dir, "x_virtual_machines.json"), 'w') as json_file:
        json.dump(confg['virtual_machines'], json_file)
    with open(os.path.join(confg_dir, "x_physical_machines.josn"), 'w') as json_file:
        json.dump(confg['physical_machines'], json_file)

# Ensure this script can be imported without running any code
if __name__ == "__main__":
    # If you want to include an example for standalone execution, you can
    # define it here. This part will only run when the script is executed directly.
    # For now, we keep it empty to focus on deployment and import use cases.
    pass
