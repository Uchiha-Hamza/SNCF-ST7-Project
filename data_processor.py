
'''
------------------------------------------------------------------------------
Ce fichier traite les données du fichier excel choisit
------------------------------------------------------------------------------
'''
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import argparse
from gurobipy import *

# Variables globales
input={
"MINI" : "mini_instance.xlsx",
"SIMPLE" : "instance_WPY_simple.xlsx",
"REALISTE" : "instance_WPY_realiste_jalon2.xlsx"}

# Choix de l'instance et du jalon 
parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('Instance', type=str, help='Choix de l\'instance : MINI, SIMPLE, REALISTE')
parser.add_argument('Jalon', type=str, help='Choix du jalon : 1, 2, 3')
# Add more arguments as needed

args = parser.parse_args()

# Access the parameters
instance_file=input[args.Instance]
JALON=int(args.Jalon)

# Lecture du fichier excel
def excel_to_dict(file: str) -> dict:
    '''
    Takes excel file name in the repo
    and returns a dictionary[sheet_name]=Dataframe
    '''
    data_dict=pd.read_excel(file, sheet_name=None)
    return data_dict

print("Lecture du fichier excel...")
INSTANCE=excel_to_dict(instance_file)

# Fonctions de conversion créneau <-> date
def date_to_creneau(date0: datetime.datetime, hour: pd.DataFrame, date: pd.DataFrame):
    '''
    Takes hour and date's 1-column dataframes
    and returns a dataframe of 1-column of 'créneaux'
    starting from date0
    '''
    # Excel is sometimes stupid and has inconsistent types
    if type(date[0])==str:
        datetime_df=pd.to_datetime(date.apply(lambda x: str(x)+' ')+hour.apply(lambda x:str(x)), dayfirst=True)
    if type(date[0])==pd._libs.tslibs.timestamps.Timestamp:
        datetime_df=pd.to_datetime(date.apply(lambda x: str(x)+' ')+hour.apply(lambda x:str(x)))
    return (datetime_df-date0).dt.total_seconds().div(60*15).astype(int)+1

def creneau_to_date(date0: datetime.datetime, creneau : int):
    return date0+ datetime.timedelta(minutes=(creneau-1)*15)

def convToStr(date)-> str:
    '''
    Takes a date in any form in the instance
    and returns a string dd/mm/yyyy
    '''
    if type(date)==str:
        return date
    else:
        return "/".join(str(date.date()).split("-")[::-1])

# Dates de début et fin de l'instance
def get_date0()->datetime.datetime:
    date0=str(INSTANCE["Sillons arrivee"]["JARR"][0])+' 00:00:00'
    date0=pd.to_datetime(date0, dayfirst=True)
    return date0-datetime.timedelta(days=float(date0.dayofweek))

def get_datef()->datetime.datetime:
    return pd.to_datetime(INSTANCE["Sillons depart"]["JDEP"].iloc[-1], dayfirst=True)+datetime.timedelta(hours=24)

print("Calcul des créneaux...")
date0=get_date0()
nombre_creneaux=int((get_datef()-date0).total_seconds()/(60*15))
INSTANCE["Sillons arrivee"]["creneau"]=date_to_creneau(date0, INSTANCE["Sillons arrivee"]["HARR"], INSTANCE["Sillons arrivee"]["JARR"])
INSTANCE["Sillons depart"]["creneau"]=date_to_creneau(date0, INSTANCE["Sillons depart"]["HDEP"], INSTANCE["Sillons depart"]["JDEP"])


# Extraction des données
def get_train_arrivee()->list:
    '''
    Prend l'instance en dictionnaire 
    et retourne la liste des trains d'arrivée
    '''
    trains_arrivee=[]
    for index, row in INSTANCE["Sillons arrivee"].iterrows():
        id_train = row['n°TRAIN'], convToStr(row["JARR"])
        trains_arrivee.append(id_train)
    return trains_arrivee

trains_arrivee=get_train_arrivee()
    
def get_train_depart()->list:
    '''
    Prend l'instance en dictionnaire 
    et retourne la liste des trains du départ
    '''
    trains_depart=[]
    for index, row in INSTANCE["Sillons depart"].iterrows():
        id_train = row['n°TRAIN'], convToStr(row["JDEP"])
        trains_depart.append(id_train)
    return trains_depart

trains_depart=get_train_depart()
    
def get_creneau_arrivee()->list:
    '''
    Prend l'instance en dictionnaire 
    et retourne la liste des créneaux d'arrivée
    '''
    creneau_arrivee={} 
    for index, row in INSTANCE["Sillons arrivee"].iterrows():
        creneau_arrivee[row["n°TRAIN"],convToStr(row["JARR"])]=row["creneau"]
    return creneau_arrivee

creneau_arrivee=get_creneau_arrivee()

def get_creaneau_depart()->list:
    '''
    Prend l'instance en dictionnaire 
    et retourne la liste des créneaux de départ
    '''
    creneau_depart={} 
    for index, row in INSTANCE["Sillons depart"].iterrows():
        creneau_depart[row["n°TRAIN"],convToStr(row["JDEP"])]=row["creneau"]
    return creneau_depart

creneau_depart=get_creaneau_depart()

def correspondances():
    '''
    Construit un dictionnaire global
    associant chaque train du départ à un set 
    des trains d'arrivée qui le constituent
    et à un train d'arrivée un set de trains 
    de départs qui lui y sont liés
    '''
    At={}
    Dt={}
    for train in trains_depart:
        At[train]=set()
    for train in trains_arrivee:
         Dt[train]=set()
    for index, row in INSTANCE["Correspondances"].iterrows():
            At[(row["n°Train depart"], convToStr(row["Jour depart"]))].add((row['n°Train arrivee'],convToStr(row['Jour arrivee'])))
            Dt[(row["n°Train arrivee"], convToStr(row["Jour arrivee"]))].add((row['n°Train depart'],convToStr(row['Jour depart'])))
            
    return At,Dt

# Dictionnarie des arrivée associées à chaque départ
At=correspondances()[0]
# Dictionarioe des départs associés à chaque arrivée
Dt=correspondances()[1]

# Créneaux de départ à partir duquel on ne peut pas dégager
# Comportant une résolution plus fine que 15 mins
creneau_precis={} # dict des paires (train: créneau précis)
for index, row in INSTANCE["Sillons depart"].iterrows():
    string=row["JDEP"]
    if type(row["JDEP"])==pd._libs.tslibs.timestamps.Timestamp:
        string=convToStr(row["JDEP"])
    date=list(map(int,string.split("/")))
    hour=list(map(int,str(row["HDEP"]).split(":")))
    date_precis=datetime.datetime(year=date[2], month=date[1], day=date[0], hour=hour[0], minute=hour[1])-datetime.timedelta(minutes=20)
    creneau_precis[row["n°TRAIN"],convToStr(row["JDEP"])]=int((date_precis-date0).total_seconds()/(60*15))+1

# Indisponibilités machines et chantiers
def creneaux_de_periode(indispo_str : str)-> list[int]: 
    plage_jours=nombre_creneaux//96
    creneaux = []
    if indispo_str!='0' and indispo_str!=0:
        periodes = indispo_str.split(';')
        for periode in periodes:
            jour, plage_horaire = periode.strip('()').split(',')
            jour = int(jour)
            jours=[jour+7*k for k in range(0,plage_jours//7+1)]
            plage_horaire = plage_horaire.strip('()').split('-')
            heure_debut, minute_debut = map(int, plage_horaire[0].split(':'))
            creneau_debut=minute_debut//15+1
            heure_fin, minute_fin = map(int, plage_horaire[1].split(':'))
            creneau_fin=minute_fin//15+1


            if (heure_debut,minute_debut)>=(heure_fin,minute_fin):
                for jour1 in jours:
                    for c in range((jour1-1)*96+heure_debut*4+creneau_debut,jour1*96):
                        if c<=nombre_creneaux:
                            creneaux.append(c)
                    for c in range(jour1*96,jour1*96+heure_fin*4+creneau_fin):
                        if c<=nombre_creneaux: creneaux.append(c)
            else:
                for jour1 in jours:
                    for c in range((jour1-1)*96+heure_debut*4+creneau_debut,(jour1-1)*96+heure_fin*4+creneau_fin):
                        if c<=nombre_creneaux: creneaux.append(c) 
    return creneaux


df = INSTANCE['Machines']

df['Indisponibilites_TimeSlots'] = df['Indisponibilites'].apply(creneaux_de_periode)

# Indiponibilités des machines
DEB_INDIS = df.loc[df['Machine'] == 'DEB', 'Indisponibilites_TimeSlots'].values[0]
FOR_INDIS = df.loc[df['Machine'] == 'FOR', 'Indisponibilites_TimeSlots'].values[0]
DEG_INDIS = df.loc[df['Machine'] == 'DEG', 'Indisponibilites_TimeSlots'].values[0]

df=INSTANCE["Chantiers"]
df['Indisponibilites']=df['Indisponibilites'].astype(str)
df['Indisponibilites_TimeSlots'] = df['Indisponibilites'].apply(creneaux_de_periode)

# Indisponibilités des chantiers
REC_INDIS = df.loc[df['Chantier'] == 'WPY_REC', 'Indisponibilites_TimeSlots'].values[0]
OFORM_INDIS = df.loc[df['Chantier'] == 'WPY_FOR', 'Indisponibilites_TimeSlots'].values[0]
DEP_INDIS = df.loc[df['Chantier'] == 'WPY_DEP', 'Indisponibilites_TimeSlots'].values[0]

# Capacités des chantiers (nombre de voies)
NVREC=df.loc[df['Chantier'] == 'WPY_REC', "Nombre de voies"].values[0]
NVFOR=df.loc[df['Chantier'] == 'WPY_FOR', "Nombre de voies"].values[0]
NVDEP=df.loc[df['Chantier'] == 'WPY_DEP', "Nombre de voies"].values[0]

# Roulements agents
Roulements_source = INSTANCE['Roulements agents']
Roulements = dict()
a = 0
i = 0
for name in Roulements_source['Roulement']:
    Roulements[name] = dict()
    Roulements[name]['Jours'] = Roulements_source['Jours de la semaine'][i].split(';')
    Roulements[name]['Nb agents'] = Roulements_source['Nombre agents'][i]
    Roulements[name]['Blocs'] = Roulements_source['Cycles horaires'][i].split(';')
    Roulements[name]['Connaissance'] = Roulements_source['Connaissances chantiers'][i].split(';')
    Blocs = dict()
    for j in Roulements[name]['Jours']: 
        for b in Roulements[name]['Blocs']:
            Blocs[(j,b)] = list()
            lbrgag = 0 #indicateur de nb de creneaux pour split des blocs de 8h
            for c in creneaux_de_periode(','.join([j, b])):
                lbrgag += 1
                if lbrgag == 33: #bloc de 8h
                    a = str(int(j) + 7) #semaine pro
                    Blocs[(a,b)] = list()
                if lbrgag >= 33: 
                    Blocs[(a,b)].append(c)
                else :
                    Blocs[(j,b)].append(c)
    i += 1
    Roulements[name]['Creneaux'] = Blocs

# Tâches humaines
roulements_rec = [a for a in Roulements.keys() if 'WPY_REC' in Roulements[a]['Connaissance']]
roulements_for = [a for a in Roulements.keys() if 'WPY_FOR' in Roulements[a]['Connaissance']]
roulements_dep = [a for a in Roulements.keys() if 'WPY_DEP' in Roulements[a]['Connaissance']]
taches_humaines={'WPY_REC': [],'WPY_FOR': [],'WPY_DEP': []}
for index, row in INSTANCE["Taches humaines"].iterrows():
            taches_humaines[row['Chantier']].append(row['Type de tache humaine'])
taches_rec=taches_humaines['WPY_REC']
taches_for=taches_humaines['WPY_FOR']
taches_dep=taches_humaines['WPY_DEP']

#Pour un agent (r,i), il faut extraire les blocs de chaque jour et puis faire les contraintes sur ces blocs:
def extraire_meme_jour(dictionnaire):
    """
    Cette fonction prend en entrée un dictionnaire dont les clés sont de la forme (roulement, agent, (jour, bloc horaire)).
    Elle extrait les couples (jour, bloc horaire) qui correspondent au même jour pour chaque (roulement, agent).
    La sortie est un dictionnaire où les clés sont les couples (roulement, agent) et les valeurs sont des dictionnaires
    dont les clés sont les jours et les valeurs sont des tuples (jour, bloc horaire) associés à ces jours pour ce couple.
    """
    result = {}
    for cle, _ in dictionnaire.items():
        roulement, agent, (jour, bloc_horaire) = cle
        cle_roulement_agent = (roulement, agent)
        if cle_roulement_agent in result:
            if jour in result[cle_roulement_agent]:
                result[cle_roulement_agent][jour].append((jour,bloc_horaire))
            else:
                result[cle_roulement_agent][jour] = [(jour,bloc_horaire)]
        else:
            result[cle_roulement_agent] = {jour: [(jour,bloc_horaire)]}

    return result
print("Données prêtes !")
print("----------------------- Info sur l'instance -------------------------")
print("Instance: ", instance_file)
print("Date de début: ", date0)
print("Date de fin: ", get_datef())
print("Nombre de créneaux: ", nombre_creneaux)
print("Nombre de trains d'arrivée: ", len(trains_arrivee))
print("Nombre de trains de départ: ", len(trains_depart))
print("---------------------------------------------------------------------")