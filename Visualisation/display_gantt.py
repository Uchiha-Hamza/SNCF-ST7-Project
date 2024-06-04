import datetime
import itertools
import os
from flask import Flask, render_template
import plotly.express as px
import pandas as pd
import argparse

# ORDERED_MACHINES = ["Debranchement", "Formation", "Degarage"]
ORDERED_MACHINES = ["DEB", "FOR", "DEG"]
MACHINE_TASKS_SHEET = "Sheet1"

Enumerate={
"MINI" : "mini_instance.xlsx",
"SIMPLE" : "instance_WPY_simple.xlsx",
"REALISTE" : "instance_WPY_realiste_jalon2.xlsx"}

parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('Instance', type=str, help='Choix de l\'instance : MINI, SIMPLE, REALISTE')
parser.add_argument('Jalon', type=str, help='Choix du jalon : 1, 2, 3')
# Add more arguments as needed

args = parser.parse_args()

# Access the parameters
instance_file=Enumerate[args.Instance]
JALON=int(args.Jalon)
result_file_name= f"solved_jalon{JALON}_{instance_file}"
result_file_name=result_file_name[:-5]

def f(date : str):
    date=list(map(int,date.split("/")))
    date_precis=datetime.datetime(year=date[2], month=date[1], day=date[0])
    return date_precis
def g(hour : str):
    hour=list(map(int,hour.split(":")))
    hour_datetime=datetime.time(hour=hour[0], minute=hour[1])
    return hour_datetime

class ResultColumnNames:
    TASK_ID = "Id tâche"
    TASK_TYPE = "Type de tâche"
    TASK_DATE = "Jour"
    TASK_HOUR = "Heure début"
    TASK_DURATION = "Durée"
    TASK_TRAIN = "Sillon"
    TASK_ArrDep = "Arr/Dep"


def get_resource_name(task_type, task_date):
    return f"{task_type} {task_date.isoformat()}"

app = Flask("app")

result_directory_path = r""
result_file_path = os.path.join(result_directory_path, "../"+result_file_name+".xlsx")

result_df = pd.read_excel(result_file_path, sheet_name=MACHINE_TASKS_SHEET)
dummy_date = datetime.date(2000, 1, 1)
tasks = []
resource_per_machine = {}
for task_id, task_type, task_pd_datetime, task_hour_datetime, task_duration, task_train, task_ArrDep in zip(
        result_df[ResultColumnNames.TASK_ID],
        result_df[ResultColumnNames.TASK_TYPE],
        result_df[ResultColumnNames.TASK_DATE],
        result_df[ResultColumnNames.TASK_HOUR],
        result_df[ResultColumnNames.TASK_DURATION],
        result_df[ResultColumnNames.TASK_TRAIN],
        result_df[ResultColumnNames.TASK_ArrDep],
):
    task_date_datetime = f(task_pd_datetime)
    task_hour_datetime = g(task_hour_datetime)
    task_start = datetime.datetime.combine(dummy_date, task_hour_datetime)
    task_resource = get_resource_name(task_type, task_date_datetime.date())
    tasks.append(
        dict(
            Train=task_train+" "+str(task_ArrDep),
            Start=task_start,
            Finish=task_start+datetime.timedelta(minutes=task_duration),
            Machine=task_type,
            Resource=task_resource,
    )
)
    resource_per_machine.setdefault(task_type, set()).add(get_resource_name(task_type, task_date_datetime.date()))
gantt_df = pd.DataFrame(tasks)
sorted_resources = list(itertools.chain.from_iterable(
    [sorted(resource_per_machine[machine]) for machine in ORDERED_MACHINES]
))
sorted_resources = sorted(sorted_resources, key=lambda x: x.split(" ")[1])[::-1]
# Creating directory of html files
if not os.path.exists(f"templates/{result_file_name}"):
    os.makedirs(f"templates/{result_file_name}")
days=[]
for i in range(len(sorted_resources)//3):
    day = sorted_resources[i*3].split(" ")[1]
    gantt_day=gantt_df[gantt_df["Resource"].str.contains(day)]
    days.append(day)
    day_resources=sorted_resources[i*3:i*3+3]
    fig = px.timeline(gantt_day, x_start="Start", x_end="Finish", y="Resource", color="Train")
    fig.update_layout(xaxis=dict(title='Timestamp', tickformat='%H:%M:%S'))
    fig.update_yaxes(categoryorder="array", categoryarray=day_resources)
    fig.write_html(f"templates/{result_file_name}/{day}.html")

days=days[::-1]
@app.route("/")
def index():
    return render_template("index.html", days=days, result_file_name=result_file_name)

@app.route('/favicon.ico')
def favicon():
    return '', 404

@app.route("/<day>")
def display_gantt(day):
    return render_template(f"{result_file_name}/{day}.html")

app.run(debug=True, port=5000)


