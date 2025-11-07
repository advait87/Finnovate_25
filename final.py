import pandas as pd


class Sumanomaly:
    def __init__(self, amount):
        self.amount = amount
        self.sum = 0
    def print(self):
        print(f"Sum: {self.amount}")


class GroupingAnomaly:
    def __init__(self, gl, gl_name, grouping_name, amount, message=None):
        self.gl = gl
        self.gl_name = gl_name
        self.grouping_name = grouping_name
        self.amount = amount
        self.message = message
    def print(self):
        print(f"GL: {self.gl}, GL Name: {self.gl_name}, Grouping: {self.grouping_name}, Amount: {self.amount}, Message: {self.message}")


allowed_zero_sum_amount_threshold = 5
dataset = pd.read_excel('trialbal.xlsx', dtype=str, header=2)

def check_anomalies(dataset, zero_sum_threshold=0):
    s = 0
    main_head = "FS Grouping Main Head"
    anomalies = []
    
    for i in range(0, len(dataset)):
        # Clean and convert Amount column
        dataset["Amount"][i] = dataset["Amount"][i].replace(",", "")
        dataset["Amount"][i] = float(dataset["Amount"][i])
        
        # Accumulate sum of amounts
        s += dataset["Amount"][i]

        grouping_name = dataset[main_head][i].strip()  # The grouping name will be from the dataset column directly

        # Check for invalid groupings
        if grouping_name not in ["Current Assets", "Non-Current Assets", "Current Liabilities", "Non-Current Liabilities", "Expenses", "Tax Expense", "Income", "Equity"]:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i], "Unknown Grouping"))
            continue

        # Check specific anomalies for each grouping type
        if grouping_name == "Current Assets" and dataset["Amount"][i] < 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Non-Current Assets" and dataset["Amount"][i] < 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Current Liabilities" and dataset["Amount"][i] > 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Non-Current Liabilities" and dataset["Amount"][i] > 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Expenses" and dataset["Amount"][i] < 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Tax Expenses" and dataset["Amount"][i] < 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Income" and dataset["Amount"][i] > 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Equity" and dataset["Amount"][i] > 0:
            anomalies.append(GroupingAnomaly(dataset["GL"][i], dataset["GL Name"][i], grouping_name, dataset["Amount"][i]))
        elif grouping_name == "Takover, Ignore" and dataset["Amount"][i] > 0:
            pass  # Ignore this case

    # If the sum of amounts exceeds the allowed threshold, add a sum anomaly
    if abs(s) > allowed_zero_sum_amount_threshold:
        anomalies.append(Sumanomaly(s))

    return anomalies

for anomaly in check_anomalies(dataset):
    anomaly.print()
    pass
