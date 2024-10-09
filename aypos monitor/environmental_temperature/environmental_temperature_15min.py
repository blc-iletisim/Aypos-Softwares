import pandas as pd
import requests as rq
import numpy as np
import time
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.initializers import Orthogonal # type: ignore
import json
from tensorflow.keras.optimizers import Adam # type: ignore
import joblib
import json
import csv
import  sys
import multiprocessing
import logging
import os


#defining functions
def process_req_now(ip):

    snmp_last_min = rq.get(ip).json()
    return snmp_last_min


def get_req_cur_1min_avg(ip):

    req = process_req_now(ip)

    # Create a DataFrame with the averaged power reading and a flag set to 0
    data = {
        'timestamp': req['time_stamp'],
        'power': req['power'],
        'flag': [0]
    }
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    
    return df


def initialize_data(file_path, ip_address, scaler):

    cur_element = get_req_cur_1min_avg(ip_address)
    selection_range = cur_element['power']

    # 30 steps in the past + script time unit
    DATA_SIZE = 30
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    df.dropna(inplace=True)
    df = df.iloc[:, 1:]
    # Calculate the bounds
    lower_bound = int(float(selection_range.values[0]) * 0.75)  # -25%
    upper_bound = int(float(selection_range.values[0]) * 1.25)  # +25%
    print(selection_range.values[0], lower_bound, upper_bound)
    s = df['power']
    len_df = len(df)
    # Filter the Series
    filtered_s = s[(s >= lower_bound) & (s <= upper_bound)]
    print('F', filtered_s, type(filtered_s), s.max())

    if len(filtered_s) < DATA_SIZE:
        diff = DATA_SIZE - len(filtered_s)
        start_point = np.random.randint(0, len_df-diff)

        # Select initial diff random rows from the DataFrame
        diff_rows = s.iloc[start_point:start_point+diff]
        initial_rows = pd.concat([filtered_s, diff_rows])
        print("S", initial_rows, type(initial_rows))
        initial_rows = scaler.fit_transform(initial_rows.values.reshape(-1, 1))

    if len(filtered_s) == DATA_SIZE:

        initial_rows = filtered_s
        print('E', initial_rows, type(initial_rows))
        initial_rows = scaler.fit_transform(initial_rows.values.reshape(-1, 1))
    
    if len(filtered_s) > DATA_SIZE:

        start_point = np.random.randint(0, len(filtered_s)-DATA_SIZE)

        # Select initial data size random rows from the DataFrame
        initial_rows = filtered_s.iloc[start_point:start_point+DATA_SIZE]
        print('L', initial_rows, type(initial_rows))
        initial_rows = scaler.fit_transform(initial_rows.values.reshape(-1, 1))
    
    initial_rows_flat = initial_rows.flatten()
    initial_rows = pd.Series(initial_rows_flat)

    return initial_rows


def update_data(data, new_element, scaler):

    DATA_SIZE = 30
    scaled_new_element = scaler.transform([new_element])
    # Append the new element to the end of the Series
    data = pd.concat([data, pd.Series([scaled_new_element[0][0]])], ignore_index=True)
    # Remove the first element to keep the size of the Series constant
    if len(data) > DATA_SIZE:
        data = data.iloc[1:] 
    return data

'''
def predict_future(model, scaler, data, seq_length, steps, window_size=3):

    predictions = []

    for i in range(steps):
        input_seq = data[-seq_length:].reshape(1, seq_length, 1)
        input_seq = np.reshape(input_seq, (1, seq_length)).astype(np.float32)
        pred = model.predict(input_seq)[0, 0]
        # Append the prediction to the data
        data = np.append(data, pred)

        # Adjust the prediction using a moving average of recent data
        if i >= window_size:
            adjustment_factor = np.mean(data[-window_size:])
            pred = (pred + adjustment_factor) / 2
        predictions.append(pred)
        #data = np.append(data, pred)

    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

    return predictions

'''


def predict_future(model, scaler, data, seq_length, steps, retrain_interval):

    predictions = []
    sliding_window = data[-seq_length:]

    for i in range(steps):
        input_seq = sliding_window.reshape(1, seq_length, 1)
        input_seq = np.reshape(input_seq, (1, seq_length)).astype(np.float32)
        pred = model.predict(input_seq)[0, 0]
        # Append the prediction to the data
        data = np.append(data, pred)

        # Update sliding window
        sliding_window = np.append(sliding_window[1:], pred)

        # Retrain the model every 'retrain_interval' steps
        if (i + 1) % retrain_interval == 0:
            recent_data = np.append(data[-(seq_length + retrain_interval):], predictions[-retrain_interval:])
            X_train = []
            y_train = []

            for j in range(len(recent_data) - seq_length):
                X_train.append(recent_data[j:j + seq_length])
                y_train.append(recent_data[j + seq_length])

            X_train = np.array(X_train).reshape(-1, seq_length, 1)
            y_train = np.array(y_train)
            # Before calling the fit method, reinitialize the optimizer
            model.compile(optimizer=Adam(), loss='mse')
            model.fit(X_train, y_train, epochs=5, verbose=0)

        predictions.append(pred)
        #data = np.append(data, pred)

    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

    return predictions, model


def calc_T_heater(power):

    power = float(power) / 2
    tcase = 0.219 * power + 52.2
    #Constants in formuls

    m_room_air = 1470 #Mass of air in the room
    c_air = 1005.4 #Specific heat capacity
    R = 4.329e-7 #Thermal resistance
    d_mass_heater = 124.68
    T_room = 24 #Initial air temperature of room
    T_outside = 24 #Outside temperature

    m_air_cond_air = 100 #Mass of air in the air conditioner
    c_air_cond_air = 1200 #Specific heat capacity of the air conditioner
    R_air_cond = 2.5e-6 #Thermal resistance of the air conditioner
    T_air_cond = 16 #Desired temperature inside the air conditioner

    dQ_loss_dt = (T_room - T_outside) / R
    dQ_gain_dt = d_mass_heater * c_air * (tcase - T_room)
    dQ_gain_air_dt = (T_air_cond - T_room) / R_air_cond
    dT_room_dt = (1 / (m_room_air * c_air)) * (dQ_gain_dt - dQ_loss_dt + dQ_gain_air_dt)

    T_heater = T_room + dT_room_dt

    return T_heater


def environmental_temperature_future_15min(cur_element, data, model, scaler, steps, retrain_interval, script_time_unit):

  # the model is trained to look at 30 steps in the past to prdict one step at the future
  seq_length = 30
  future_steps = steps
  predicted_values, model = predict_future(model, scaler, data.values, seq_length, future_steps, retrain_interval)
  print(predicted_values)
  power_future_15min = list(predicted_values)[-1]
  T_heater_15min = calc_T_heater(power_future_15min)
  T_heater_cur = calc_T_heater(cur_element['power'])
  cur_element['env_temp_cur'] = T_heater_cur
  ###
  cur_element['now_timestamp'] = pd.to_datetime(cur_element.index)
  ###
  cur_element['future_timestamp'] = pd.to_datetime(cur_element.index) + pd.to_timedelta((script_time_unit // 60) * steps, unit='m')
  cur_element['env_temp_15min'] = T_heater_15min
  cur_element['power_future_15min'] = power_future_15min
  

  return cur_element, model


def flag_check(data_list, cur_element):
    

    print("this is history:", data_list)
        # Check if the timestamps match
    if cur_element['now_timestamp'].iloc[0] in data_list.keys():

        first_element = data_list[cur_element['now_timestamp'].iloc[0]]
            # Compare the env_temp values
        print('you are here')
        
        if (cur_element['env_temp_cur'].values[0] > first_element['env_temp_15min'].values[0]) or (cur_element['env_temp_cur'].values[0]>28.3):

            cur_element['flag'] = int((cur_element['env_temp_cur'].values[0] - cur_element['env_temp_cur'].values[0])+1)

        else:
            # Set flag to 0 if not
            cur_element['flag'] = "it is fine"

            # Set flag to 1 if cur_element's env_temp_cur is greater
            
        # Remove the first element from the list
        data_list.pop(cur_element['now_timestamp'].iloc[0])
        
        # Return the new element
        return cur_element, data_list
    else:
        # Set flag to 0 if not
        cur_element['flag'] = "still not time yet"
    
    # Return the new element
    return cur_element, data_list
    

##################################################################################################
#one time calling functions

def script_initializer(user_inputs):

    congf_file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\environmental_temperature\\script_config.json'

    # Open the JSON file
    with open(congf_file_path, 'r') as file:
        # Load the JSON data
        script_confg = json.load(file)

    steps = int(user_inputs['number_of_steps'])
    get_snmp_ip_address = script_confg['ip_addresses']['get_ip_addresses']['snmp_ip_address']
    scaler_file_path = script_confg['scaler_type'][user_inputs['script_time_unit']]
    scaler = joblib.load(scaler_file_path)
    initial_rows_file_path = script_confg['initial_rows_type'][user_inputs['script_time_unit']]
    start_data = initialize_data(initial_rows_file_path, get_snmp_ip_address, scaler)
    len_start_data = len(start_data)
    model_file_path = script_confg['models'][user_inputs['script_time_unit']][user_inputs['model_type']]
    model = tf.keras.models.load_model(model_file_path, custom_objects={'Orthogonal': Orthogonal})
    last_15_elements = {}
    post_ip_address = script_confg['ip_addresses']['post_ip_addresses']['horizon_ip_address']
    retrain_interval = steps //3
    script_time_unit = int(user_inputs['script_time_unit']) * 60

    connection, updated_data = connect(get_snmp_ip_address, start_data, scaler)

    parameters = (get_snmp_ip_address, start_data, scaler, steps, model, post_ip_address, last_15_elements, initial_rows_file_path, model_file_path, len_start_data, retrain_interval, connection, updated_data, script_time_unit)

    return parameters

def script_finalizer(initial_rows_file_path, model_file_path, updated_data, len_start_data, model):

    model.save(model_file_path)
    updated_data = updated_data.to_frame()
    headers = updated_data.columns

    with open(initial_rows_file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        
        # If the file does not exist, write the header
        if not initial_rows_file_path:
            writer.writerow(headers)
        
        # Write new rows
        writer.writerows(updated_data.iloc[len_start_data:]['power'].to_list())


##################################################################################################
#CPT functions  

def connect(connection_condition, data, scaler):

    cur_element = get_req_cur_1min_avg(connection_condition)

    updated_data = update_data(data, cur_element['power'], scaler)

    return cur_element, updated_data


def process(connection, data, model, scaler, steps, last_15_elements, retrain_interval, script_time_unit):

    cur_element, model = environmental_temperature_future_15min(connection, data, model, scaler, steps, retrain_interval, script_time_unit)
    last_15_elements[cur_element['future_timestamp'].iloc[0]] = cur_element
    env_temp, last_15_elements = flag_check(last_15_elements, cur_element)

    return env_temp, model, last_15_elements


def transact(a_process, api_url):

    # commanted out for fastapi, fastapi needs to be updated before running down 2 lines
    #a_process.pop('power')
    
    a_process_dict = a_process.to_dict(orient='records')

    # Convert all values to strings
    a_process_dict_str = [{k: str(v) for k, v in record.items()} for record in a_process_dict]

    print("::::", a_process_dict_str)
        
    return rq.post(api_url, json=a_process_dict_str[0])    


def write_to_csv(value, file_path='C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\environmental_temperature\\current_output.csv'):
    # Check if the file exists
    
    # Open the file in append mode
    value.to_csv(file_path)



def delete_file_if_exists(file_path= 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\environmental_temperature\\current_output.csv'):
    if os.path.isfile(file_path):
        os.remove(file_path)

file_path = 'C:\\Users\\B_L_C\\Desktop\\aypos_monitor\\environmental_temperature\\current_output.csv'


def main_e(user_inputs):
    
    # Send data to the FastAPI app every 1 minute

    parameters = script_initializer(user_inputs)

    get_snmp_ip_address, start_data, scaler, steps, model, post_ip_address, last_15_elements, initial_rows_file_path, model_file_path, len_start_data, retrain_interval, connection, updated_data, script_time_unit = parameters

    connection, updated_data = connect(get_snmp_ip_address, updated_data, scaler)
    a_process, model, last_15_elements = process(connection, updated_data, model, scaler, steps, last_15_elements, retrain_interval, script_time_unit)
    temp_a_process = a_process
    write_to_csv(temp_a_process)
    response = transact(a_process, post_ip_address)

    print(f"M_VAR:{a_process}")
    # Write `m` to the CSV file
    write_to_csv(a_process)

    print("Response from API:", response.json())
    # if prints the data its ok, if writes internal error, there is a problem and its ok
    time.sleep(script_time_unit)

    print(parameters)

    try:

        while True:

            connection, updated_data = connect(get_snmp_ip_address, updated_data, scaler)
            a_process, model, last_15_elements = process(connection, updated_data, model, scaler, steps, last_15_elements, retrain_interval, script_time_unit)
            response = transact(a_process, post_ip_address)

            print(f"M_VAR:{a_process}")
            # Write `m` to the CSV file

            temp_a_process = pd.concat([temp_a_process, a_process], ignore_index=True)
            print(f'###############{temp_a_process}#############')
            write_to_csv(temp_a_process)

            print("Response from API:", response.json())
             # if prints the data its ok, if writes internal error, there is a problem and its ok
            time.sleep(script_time_unit)

    except KeyboardInterrupt:
        print("Process interrupted. Cleaning up...")
    except Exception as e:
        print("Exception: ", e)
    finally:
        # Ensure the file is deleted when the script ends or is interrupted
        delete_file_if_exists()
        #script_finalizer(initial_rows_file_path, model_file_path, updated_data, len_start_data, model)

       



if __name__ == "__main__":
    import sys
    import json
    from multiprocessing import Queue
    import os

    # Unpack arguments from the main script

    #user_inputs = json.loads(sys.argv[1])
    user_inputs = {
        'number_of_steps': '3',
        'script_time_unit': '1',
        'model_type': 'lstm'
    }

    # Run the main function
    main_e(user_inputs)