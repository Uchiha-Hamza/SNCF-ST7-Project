'''
------------------------------------------------------------------------------
Après avoir choisi l'instance à optimiser dans le fichier data_processor.py,
ce fichier optimize l'instance choisie et enregistre les résultats dans un 
fichier excel.
------------------------------------------------------------------------------
'''
from data_processor import *
import matplotlib.pyplot as plt

'''-------------------------------Définition des variables-------------------------------'''
print("Initialisation des variables...")
m= Model('Modèle')

# machine_(train, creneau) = 1 si la machine travail sur le train dans ce créneau 
deb = {(i, c) : m.addVar(vtype = GRB.BINARY, name=f'deb_{i}_{c}') for i in trains_arrivee for c in range(1,nombre_creneaux+1)}
form = {(i, c) : m.addVar(vtype = GRB.BINARY, name=f'form_{i}_{c}') for i in trains_depart for c in range(1,nombre_creneaux+1)}
deg = {(i, c) : m.addVar(vtype = GRB.BINARY, name=f'deg_{i}_{c}') for i in trains_depart for c in range(1,nombre_creneaux+1)}

# occupationChantier_(train, creneau) = 1 si le train est sur le chantier dans ce créneau
orec = {(i, c) : m.addVar(vtype = GRB.BINARY, name=f'orec_{i}_{c}') for i in trains_arrivee for c in range(1,nombre_creneaux+1)}
oform = {(i, c) : m.addVar(vtype = GRB.BINARY, name=f'oform_{i}_{c}') for i in trains_depart for c in range(1,nombre_creneaux+1)}
odep = {(i, c) : m.addVar(vtype = GRB.BINARY, name=f'odep_{i}_{c}') for i in trains_depart for c in range(1,nombre_creneaux+1)}

# tâche_hum_(tâche, train, roulement, agent, creneau) = 1 
# si l'agent travaille sur la tâche du train dans ce créneau
taches_hum_rec = {(tache,train,roulement,agent,c) : m.addVar(vtype = GRB.BINARY, name=f'{tache}_{train}_{roulement}_{agent}_{c}') for tache in taches_rec for train in trains_arrivee for roulement in roulements_rec for agent in range(1,Roulements[roulement]['Nb agents']+1) for c in range(1,nombre_creneaux+1)}
taches_hum_for = {(tache,train,roulement,agent,c) : m.addVar(vtype = GRB.BINARY, name=f'{tache}_{train}_{roulement}_{agent}_{c}') for tache in taches_for for train in trains_depart for roulement in roulements_for for agent in range(1,Roulements[roulement]['Nb agents']+1) for c in range(1,nombre_creneaux+1)}
taches_hum_dep = {(tache,train,roulement,agent,c) : m.addVar(vtype = GRB.BINARY, name=f'{tache}_{train}_{roulement}_{agent}_{c}') for tache in taches_dep for train in trains_depart for roulement in roulements_dep for agent in range(1,Roulements[roulement]['Nb agents']+1) for c in range(1,nombre_creneaux+1)}

# Nombre de tâches effectuées par un agent
nb_taches_rec={(r,i,b): quicksum([taches_hum_rec[(tache,t,r,i,c)] for tache in taches_rec for t in trains_arrivee for c in Roulements[r]['Creneaux'][b]])   for r in roulements_rec for i in range(1,Roulements[r]['Nb agents']+1) for b in Roulements[r]['Creneaux']}
nb_taches_for={(r,i,b): quicksum([taches_hum_for[(tache,t,r,i,c)] for tache in taches_for for t in trains_depart for c in Roulements[r]['Creneaux'][b]])   for r in roulements_for for i in range(1,Roulements[r]['Nb agents']+1) for b in Roulements[r]['Creneaux']}
nb_taches_dep={(r,i,b): quicksum([taches_hum_dep[(tache,t,r,i,c)] for tache in taches_dep for t in trains_depart for c in Roulements[r]['Creneaux'][b]])   for r in roulements_dep for i in range(1,Roulements[r]['Nb agents']+1) for b in Roulements[r]['Creneaux']}

#certaines tâches vont se compter plusieurs fois (tâches nécessitant Dt>c)...
def fusion_dictionnaires(*dicts):
    result = {}
    for d in dicts:
        for key, value in d.items():
            result[key] = result.get(key, 0) + value
    return result

# dict({(roulement, agent, bloc) : nombre de tâches effectuées par l'agent})
# Où bloc = (jour, bloc horaire)
nb_taches=fusion_dictionnaires(nb_taches_rec,nb_taches_for,nb_taches_dep)

'''-------------------------------Définition des contraintes-------------------------------'''
print("Définition des contraintes...")
# Unique tâche machine par train
uniqueDeb_train = {i : m.addConstr(quicksum([deb[(i, c)] for c in range(1, nombre_creneaux + 1)]) ==1, name = f'UniqueDeb_train{i}') for i in trains_arrivee}
uniqueform_train = {i : m.addConstr(quicksum([form[(i, c)] for c in range(1, nombre_creneaux + 1)]) ==1, name = f'UniqueFor_train{i}') for i in trains_depart}
uniqueDeg_train = {i : m.addConstr(quicksum([deg[(i, c)] for c in range(1, nombre_creneaux + 1)]) ==1, name = f'UniqueDeg_train{i}') for i in trains_depart}

# Une seule tâche machine par créneau
uniqueDeb_creneau = {c : m.addConstr(quicksum([deb[(i, c)] for i in trains_arrivee]) <=1, name = f'UniqueDeb_creneau{c}') for c in range(1, nombre_creneaux + 1)}
uniqueFor_creneau = {c : m.addConstr(quicksum([form[(i, c)] for i in trains_depart]) <=1, name = f'UniqueFor_creneau{c}') for c in range(1, nombre_creneaux + 1)}
uniqueDeg_creneau = {c : m.addConstr(quicksum([deg[(i, c)] for i in trains_depart ]) <=1, name = f'UniqueDeg_creneau{c}') for c in range(1, nombre_creneaux + 1)}

# Débranchement après l'arrivée
deb_apres_arrivee = {i : m.addConstr(quicksum([deb[(i, c)] for c in range(1, creneau_arrivee[i] + 5)]) ==0, name = f'deb_apres_arrivee{i}') for i in trains_arrivee}

# Formation d'un train de départ
for_apres_deb = {(t,c,i) : m.addConstr(form[(t,c)]<=quicksum([deb[(i, c_p)] for c_p in range(1, c)]), name = f'for_apres_deb{t}{c}{i}') for t in trains_depart for c in range(1,nombre_creneaux+1) for i in At[t]}

# Dégarage après formation
deg_apres_for = {(t,c) : m.addConstr(deg[(t,c)]<=quicksum([form[(t, c_p)] for c_p in range(1, c-9)]), name = f'deg_apres_for{t},{c}') for t in trains_depart for c in range(1,nombre_creneaux+1)}

# Dégarage ne peut pas avoir lieu avant départ-20mins
deg_avant_depart = {t : m.addConstr(quicksum([deg[(t, c)] for c in range(creneau_depart[t]-2, nombre_creneaux+1)])==0, name = f'depart_apres_deg{t}') for t in trains_depart}

# Disponibilité des machines
indisponibilite_deb = {i : m.addConstr(quicksum([deb[(i, c)] for c in DEB_INDIS]) ==0, name = f'indisponibilité_deb{i}') for i in trains_arrivee }
indisponibilite_for = {i : m.addConstr(quicksum([form[(i, c)] for c in FOR_INDIS]) ==0, name = f'indisponibilité_for{i}') for i in trains_depart}
indisponibilite_deb = {i : m.addConstr(quicksum([deg[(i, c)] for c in DEG_INDIS]) ==0, name = f'indisponibilité_deg{i}') for i in trains_depart}

if JALON==2 or JALON==3:
    # Capacité des chantiers
    Nb_voies_rec = {c : m.addConstr(quicksum([orec[(i, c)] for i in trains_arrivee]) <= NVREC, name = f'nb_voies_rec{c}') for c in range(1,nombre_creneaux+1) }
    Nb_voies_for = {c : m.addConstr(quicksum([oform[(i, c)] for i in trains_depart]) <= NVFOR, name = f'nb_voies_form{c}') for c in range(1,nombre_creneaux+1) }
    Nb_voies_dep = {c : m.addConstr(quicksum([odep[(i, c)] for i in trains_depart]) <= NVDEP, name = f'nb_voies_dep{c}') for c in range(1,nombre_creneaux+1) }

    # Indisponibilité des chantiers
    indisponibilite_orec = {i : m.addConstr(quicksum([orec[(i, c)] for c in REC_INDIS]) ==0, name = f'indisponibilité_rec{i}') for i in trains_arrivee }
    indisponibilite_oform = {i : m.addConstr(quicksum([oform[(i, c)] for c in OFORM_INDIS]) ==0, name = f'indisponibilité_oform{i}') for i in trains_depart}
    indisponibilite_dep = {i : m.addConstr(quicksum([odep[(i, c)] for c in DEP_INDIS]) ==0, name = f'indisponibilité_dep{i}') for i in trains_depart}

    # Occupation du chantier de la réception
    M=(nombre_creneaux)**2
    eps=0.1
    creneau_deb={i : quicksum([u*deb[(i,u)] for u in range(1,nombre_creneaux+1)]) for i in trains_arrivee}
    occupation_arrivee_deb={(i,c) : m.addConstr((eps+(c-creneau_arrivee[i]))*(creneau_deb[i]-c+eps)<=M*orec[(i,c)], name=f'occupation_arrivee_deg_{i,c}') for i in trains_arrivee for c in range(1,1+nombre_creneaux)}

    # Débranchement => occupation du chantier de la formation
    reserve_voies_for_au_deb = {(t,c,i) : m.addConstr(deb[(t,c)]<=oform[(i,c)], name = f'reserve_voies_for_au_deb{t}{c}{i}') for t in trains_arrivee for c in range(1,nombre_creneaux+1) for i in Dt[t]}

    # Occupation du chantier de la formation
    z = {(t, c) : m.addVar(vtype = GRB.BINARY, name=f'z_{t}_{c}') for t in trains_depart for c in range(1,nombre_creneaux)}
    duree_occupe_form1={(t,c): m.addConstr(z[(t,c)]<=oform[(t,c)], name = f'duree_occupe_form1{t,c}') for t in trains_depart for c in range(1,nombre_creneaux)}
    duree_occupe_form2={(t,c): m.addConstr(z[(t,c)]<=1-deg[(t,c)], name = f'duree_occupe_form2{t,c}') for t in trains_depart for c in range(1,nombre_creneaux)}
    duree_occupe_form3={(t,c): m.addConstr(z[(t,c)]>=oform[(t,c)]-deg[(t,c)], name = f'duree_occupe_form3{t,c}') for t in trains_depart for c in range(1,nombre_creneaux)}
    duree_occupe_form4={(t,c): m.addConstr(z[(t,c)]<=oform[(t,c+1)], name = f'duree_occupe_form4{t,c}') for t in trains_depart for c in range(1,nombre_creneaux)}

    # Dégarage => occupation du chantier de la formation
    reserve_voie_for_au_deg = {(t,c) : m.addConstr(deg[(t,c)]<=oform[(t,c)], name = f'reserve_voie_for_au_deg{t}{c}') for t in trains_depart for c in range(1,nombre_creneaux+1)}

    # Créneaux où on libère les voies de la formation
    creneau_deg={i : quicksum([u*deg[(i,u)] for u in range(1,nombre_creneaux+1)]) for i in trains_depart}
    non_occupation_for_apres_deg={(t,c) : m.addConstr((c-creneau_deg[t])<=M*(1-oform[(t,c)]), name=f'occupation_for_qd_deg_{t,c}') for t in trains_depart for c in range(1,1+nombre_creneaux)}

    # Occupation du chantier de la départ
    M=(nombre_creneaux)**2
    eps=0.1
    occupation_deg_depart={(i,c) : m.addConstr((eps+creneau_depart[i]-c)*(c-creneau_deg[i]+eps)<=M*odep[(i,c)], name=f'occupation_deg_depart_{i,c}') for i in trains_depart for c in range(1,1+nombre_creneaux)}

    if JALON==3:
        # On définit des variables auxiliaires
        # On raisonne sur chaque train $t$ et créneau c pour savoir si la tâche humaine s'effectue sur le train t au créneau c
        taches_hum_arr_tc = {(tache,train,c) : quicksum([taches_hum_rec[(tache,train,roulement,i,c)] for roulement in roulements_rec for i in range(1,Roulements[roulement]['Nb agents']+1)])   for train in trains_arrivee  for tache in taches_rec for c in range(1,nombre_creneaux+1)}
        taches_hum_for_tc = {(tache,train,c) : quicksum([taches_hum_for[(tache,train,roulement,i,c)] for roulement in roulements_for for i in range(1,Roulements[roulement]['Nb agents']+1)])   for train in trains_depart  for tache in taches_for for c in range(1,nombre_creneaux+1)}
        taches_hum_dep_tc = {(tache,train,c) : quicksum([taches_hum_dep[(tache,train,roulement,i,c)] for roulement in roulements_dep for i in range(1,Roulements[roulement]['Nb agents']+1)])   for train in trains_depart  for tache in taches_dep for c in range(1,nombre_creneaux+1)}

        # Un agent travaille pendant un bloc horraire pendant 
        # au plus une journée de service
        agents_jours_blocs = extraire_meme_jour(nb_taches)

        agent_rec_work_bloc={(agent,jour,tache,train,c,J1): m.addConstr(quicksum([nb_taches[(agent[0],agent[1],J)] for J in agents_jours_blocs[agent][jour] if J!=J1]) <=M*(1-taches_hum_rec[(tache,train,agent[0],agent[1],c)]),name = f'agent_rec_work_bloc_{agent}_{jour}_{tache}_{train}_{c}_{J1}') for agent in agents_jours_blocs if agent[0] in roulements_rec for jour in agents_jours_blocs[agent] for J1 in agents_jours_blocs[agent][jour] for c in Roulements[agent[0]]['Creneaux'][J1] for train in trains_arrivee for tache in taches_rec}
        agent_for_work_bloc={(agent,jour,tache,train,c,J1): m.addConstr(quicksum([nb_taches[(agent[0],agent[1],J)] for J in agents_jours_blocs[agent][jour] if J!=J1]) <=M*(1-taches_hum_for[(tache,train,agent[0],agent[1],c)]),name = f'agent_for_work_bloc_{agent}_{jour}_{tache}_{train}_{c}_{J1}') for agent in agents_jours_blocs if agent[0] in roulements_for for jour in agents_jours_blocs[agent] for J1 in agents_jours_blocs[agent][jour] for c in Roulements[agent[0]]['Creneaux'][J1] for train in trains_depart for tache in taches_for}
        agent_dep_work_bloc={(agent,jour,tache,train,c,J1): m.addConstr(quicksum([nb_taches[(agent[0],agent[1],J)] for J in agents_jours_blocs[agent][jour] if J!=J1]) <=M*(1-taches_hum_dep[(tache,train,agent[0],agent[1],c)]),name = f'agent_dep_work_bloc_{agent}_{jour}_{tache}_{train}_{c}_{J1}') for agent in agents_jours_blocs if agent[0] in roulements_dep for jour in agents_jours_blocs[agent] for J1 in agents_jours_blocs[agent][jour] for c in Roulements[agent[0]]['Creneaux'][J1] for train in trains_depart for tache in taches_dep}

        # Chaque tâche humaine est réalisée par un seul agent dans un seul créneau
        tache_realisee_1_agent_rec={(train,tache): m.addConstr(quicksum([taches_hum_rec[(tache,train,agent[0],agent[1],c)] for agent in agents_jours_blocs if agent[0] in roulements_rec for c in range(1,nombre_creneaux+1)])==1,name = f'tache_realisee_1_agent_rec_{train}_{tache}') for train in trains_arrivee for tache in taches_rec}
        tache_realisee_1_agent_for={(train,tache): m.addConstr(quicksum([taches_hum_for[(tache,train,agent[0],agent[1],c)] for agent in agents_jours_blocs if agent[0] in roulements_for for c in range(1,nombre_creneaux+1)])==1,name = f'tache_realisee_1_agent_for_{train}_{tache}') for train in trains_depart for tache in taches_for}
        tache_realisee_1_agent_dep={(train,tache): m.addConstr(quicksum([taches_hum_dep[(tache,train,agent[0],agent[1],c)] for agent in agents_jours_blocs if agent[0] in roulements_dep for c in range(1,nombre_creneaux+1)])==1,name = f'tache_realisee_1_agent_dep_{train}_{tache}') for train in trains_depart for tache in taches_dep}

        # Un agent effectue au plus une tâche par créneau
        # On definit comme auparavant le nombre de taches effectués par un agent mais cette fois pendant un seul créneau
        nb_taches_rec_c={(r,i,c): quicksum([taches_hum_rec[(tache,t,r,i,c)] for tache in taches_rec for t in trains_arrivee])   for r in roulements_rec for i in range(1,Roulements[r]['Nb agents']+1) for c in range(1, nombre_creneaux+1)}
        nb_taches_for_c={(r,i,c): quicksum([taches_hum_for[(tache,t,r,i,c)] for tache in taches_for for t in trains_depart])   for r in roulements_for for i in range(1,Roulements[r]['Nb agents']+1) for c in range(1, nombre_creneaux+1)}
        nb_taches_dep_c={(r,i,c): quicksum([taches_hum_dep[(tache,t,r,i,c)] for tache in taches_dep for t in trains_depart])   for r in roulements_dep for i in range(1,Roulements[r]['Nb agents']+1) for c in range(1, nombre_creneaux)}

        nb_taches_c=fusion_dictionnaires(nb_taches_rec_c,nb_taches_for_c,nb_taches_dep_c)

        une_tache_au_plus_par_c={(r,i,c): m.addConstr(nb_taches_c[(r,i,c)]<=1 ,name = f'une_tache_au_plus_par_c_{r}_{i}_{c}') for r,i,c in nb_taches_c.keys()}

        # Ordre séquentiel des tâches humaines
        #REC
        arrivee_avant_rec={t: m.addConstr(quicksum([c*taches_hum_arr_tc[('arrivée Reception',t,c)] for c in range(1,nombre_creneaux+1)])>=creneau_arrivee[t],name = f'arrivee_avant_rec_{t}') for t in trains_arrivee}
        rec_avant_tri={t: m.addConstr(quicksum([c*taches_hum_arr_tc[('arrivée Reception',t,c)] for c in range(1,nombre_creneaux+1)])<=quicksum([c*taches_hum_arr_tc[('préparation tri',t,c)] for c in range(1,nombre_creneaux+1)])-1,name = f'rec_avant_tri_{t}') for t in trains_arrivee}
        tri_avant_deb={t: m.addConstr(quicksum([c*taches_hum_arr_tc[('préparation tri',t,c)] for c in range(1,nombre_creneaux+1)])<=quicksum([c*taches_hum_arr_tc[('débranchement',t,c)] for c in range(1,nombre_creneaux+1)])-1,name = f'tri_avant_deb_{t}') for t in trains_arrivee}
        #FOR
        appui_avant_attelage={t: m.addConstr(quicksum([c*taches_hum_for_tc[('appui voie + mise en place câle',t,c)] for c in range(1,nombre_creneaux+1)])<=quicksum([c*taches_hum_for_tc[('attelage véhicules',t,c)] for c in range(1,nombre_creneaux+1)])-1,name = f'appui_avant_atelage_{t}') for t in trains_depart}
        attelage_avant_deg={t: m.addConstr(quicksum([c*taches_hum_for_tc[('attelage véhicules',t,c)] for c in range(1,nombre_creneaux+1)])<=quicksum([c*taches_hum_for_tc[('dégarage / bouger de rame',t,c)] for c in range(1,nombre_creneaux+1)])-1,name = f'attelage_avant_deg_{t}') for t in trains_depart}
        #DEP
        deg_avant_essai_frein={t: m.addConstr(quicksum([c*taches_hum_for_tc[('dégarage / bouger de rame',t,c)] for c in range(1,nombre_creneaux+1)])<=quicksum([c*taches_hum_dep_tc[('essai de frein départ',t,c)] for c in range(1,nombre_creneaux+1)])-1,name = f'deg_avant_essai_frein_{t}') for t in trains_depart}

        # Parallélisation des tâches humaines || tâches machine	
        debranchement_deb={(t,c): m.addConstr(taches_hum_arr_tc[('débranchement',t,c)]==deb[(t,c)],name = f'debranchement_deb_{t}') for t in trains_arrivee for c in range(1,nombre_creneaux+1)}
        appui_for={(t,c): m.addConstr(taches_hum_for_tc[('appui voie + mise en place câle',t,c)]==form[(t,c)],name = f'appui_for_{t}') for t in trains_depart for c in range(1,nombre_creneaux+1)}
        bouger_deg={(t,c): m.addConstr(taches_hum_for_tc[('appui voie + mise en place câle',t,c)]==deg[(t,c)],name = f'bouger_deg_{t}') for t in trains_depart for c in range(1,nombre_creneaux+1)}

        # Indisponibilité des chantiers
        indispo_rec_hum={(r,i): m.addConstr(quicksum([nb_taches_rec_c[(r,i,c)] for c in REC_INDIS])==0,name = f'indispo_rec_hum={r}_{i}') for r in roulements_rec for i in range(1,Roulements[r]['Nb agents']+1)}
        indispo_for_hum={(r,i): m.addConstr(quicksum([nb_taches_for_c[(r,i,c)] for c in OFORM_INDIS])==0,name = f'indispo_for_hum={r}_{i}') for r in roulements_for for i in range(1,Roulements[r]['Nb agents']+1)}
        indispo_dep_hum={(r,i): m.addConstr(quicksum([nb_taches_dep_c[(r,i,c)] for c in DEP_INDIS])==0,name = f'indispo_dep_hum={r}_{i}') for r in roulements_dep for i in range(1,Roulements[r]['Nb agents']+1)}

        # Un agent ne travaille que pendant ses blocs horaires
        indispo_agent = {(r,i): m.addConstr(quicksum([nb_taches_c[(r,i,c)] for c in range(1, nombre_creneaux+1)]) >= quicksum([nb_taches[(r,i,b)] for b in Roulements[r]['Creneaux']]),name = f'indispo_agent_{r}_{i}') for r in Roulements for i in range(1,Roulements[r]['Nb agents']+1)}


'''-------------------------------Résolution-------------------------------'''
if JALON==1:
    m.setObjective(1, GRB.MINIMIZE)

if JALON==2 or JALON==3:

    # Minimization des taux d'occupation des chantiers
    objfunction_for = quicksum([oform[(t,c)] for t in trains_depart for c in range(1,nombre_creneaux+1)])
    objfunction_dep = quicksum([odep[(t,c)] for t in trains_depart for c in range(1,nombre_creneaux+1)])
    objfunction_rec = quicksum([orec[(t,c)] for t in trains_arrivee for c in range(1,nombre_creneaux+1)])
    if JALON==2:
        m.setObjective(objfunction_for+objfunction_dep+objfunction_rec, GRB.MINIMIZE)

    if JALON==3:
        # Pour définir la fonction objectif, on a besoin 
        # d'introduire des variables auxiliaires
        nb_taches_jour={(r,i,j): quicksum([nb_taches[(r,i,b)] for b in Roulements[r]['Creneaux']]) for r,i,_ in nb_taches.keys() for j in Roulements[r]['Jours']}
        travaille_jour={(r,i,j): m.addVar(vtype = GRB.BINARY, name=f'travaille_{r},{i}_{j}') for r,i,_ in nb_taches.keys() for j in Roulements[r]['Jours'] }
        contrainte_travaille={(r,i,j): m.addConstr(nb_taches_jour[(r,i,j)]<=travaille_jour[(r,i,j)]*M,name = f'contrainte_travaille_{r}_{i}_{j}') for r,i,_ in nb_taches.keys() for j in Roulements[r]['Jours'] }

        # On minimize le nombre des journée de service
        # Pour chaque couple (roulement, agent)
        objfunction_jalon3=quicksum([travaille_jour[(r,i,j)] for r,i,_ in nb_taches.keys() for j in Roulements[r]['Jours']])

        m.setObjective(objfunction_for+objfunction_dep+objfunction_rec+objfunction_jalon3, GRB.MINIMIZE)

m.params.OutputFlag = 0
print("Mise en place des contraintes...")
m.update()

print("Optimisation en cours...")
m.optimize()
print("Optimisation terminée...")
if JALON==2:
    print("--------------------------- Valeur optimale de la fonction objectif ---------------------------")
    print("Nombre de voies occupées par les chantiers :", m.objVal)
    print("Visualization du taux d'occupation du chantier de formation...")
    X=range(1, nombre_creneaux+1)
    Y=[sum([oform[(t,c)].x for t in trains_depart]) for c in X]
    plt.bar(X, Y)

    # Add labels and title
    plt.xlabel('Créneau horaire de 15 minutes')
    plt.ylabel('Nombre de voies occupés dans WPY_FOR')
    plt.title('Occupation des voies par chantier de formation')

    # Show plot
    plt.show()
SOLVED=True

'''-------------------------------Logging en cas d'échec-------------------------------'''
if m.status == GRB.INF_OR_UNBD:
    SOLVED=False

if m.status == GRB.INFEASIBLE:
    print("Pas de solution trouvée...")
    SOLVED=False
    print("Calcul de contraintes contradictoires...")
    m.computeIIS()
    log_file = open('gurobi_log.txt', 'w')
    log_file.write(f"Instance : {instance_file}\n")
    log_file.write(f"Jalon : {JALON}\n")
    log_file.write(f"Contraintes en conflit :\n")
    total=0
    for c in m.getConstrs():
        if c.IISConstr:
            total+=1
            log_file.write(f'{c.constrName}\n')

            
elif m.status == GRB.UNBOUNDED:
    print("\n\tEST NON BORNÉ!!!")
'''-------------------------------Enregistrement des résultats-------------------------------'''
print("Enregistrement des résultats...")
if SOLVED:
    outputxlsx = f"solved_jalon{JALON}_{instance_file}"
    if JALON==1:
        output = {'Id tâche': [], 'Type de tâche' : [], 'Jour' : [], 'Arr/Dep' : [],
                  'Heure début' : [], 'Durée' : [], 'Sillon' : []}
        for train in trains_arrivee:
            for c in range(1,nombre_creneaux+1):
                if deb[(train,c)].x==1:
                    output['Id tâche'].append(f'DEB_{train[0]}_'+ creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Type de tâche'].append('DEB')
                    output['Jour'].append(creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Arr/Dep'].append(creneau_to_date(date0, creneau_arrivee[train]))
                    output['Heure début'].append(creneau_to_date(date0, c).strftime('%H:%M'))
                    output['Durée'].append(15)
                    output['Sillon'].append(train[0])


        for train in trains_depart:
            for c in range(1,nombre_creneaux+1):
                if form[(train,c)].x==1:
                    output['Id tâche'].append(f'FOR_{train[0]}_'+ creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Type de tâche'].append('FOR')
                    output['Jour'].append(creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Arr/Dep'].append(creneau_to_date(date0, creneau_depart[train]))
                    output['Heure début'].append(creneau_to_date(date0, c).strftime('%H:%M'))
                    output['Durée'].append(15)
                    output['Sillon'].append(train[0])
                if deg[(train,c)].x==1:
                    output['Id tâche'].append(f'DEG_{train[0]}_' + creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Type de tâche'].append('DEG')
                    output['Jour'].append(creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Arr/Dep'].append(creneau_to_date(date0, creneau_depart[train]))
                    output['Heure début'].append(creneau_to_date(date0, c).strftime('%H:%M'))
                    output['Durée'].append(15)
                    output['Sillon'].append(train[0])
        # Piping output into an excel sheet
        print(f"Résultats enregistrés dans le fichier {outputxlsx}")
        outputdf=pd.DataFrame(output)
        outputdf.to_excel(outputxlsx, index=False)
    if JALON==2:
        output = {'Id tâche': [], 'Type de tâche' : [], 'Jour' : [], 'Arr/Dep' : [],'Heure début' : [], 'Durée' : [], 'Sillon' : [],
                'Occupation des voies par chantier (optim)': [], 'WPY_REC' : [], 'WPY_FOR' : [], 'WPY_DEP' : []}
        nb_voie_occ={"WPY_REC": [],
                    "WPY_FOR": [],
                    "WPY_DEP": []}
        for c in range(1,1+nombre_creneaux):
            # Occupation des voies
            nb_voie_occ["WPY_REC"].append(sum([orec[(t,c)].x for t in trains_arrivee]))
            nb_voie_occ["WPY_FOR"].append(sum([oform[(t,c)].x for t in trains_depart]))
            nb_voie_occ["WPY_DEP"].append(sum([odep[(t,c)].x for t in trains_depart]))
            
            # Tâches machines sur les trains d'arrivee 
            for train in trains_arrivee:
                if deb[(train,c)].x==1:
                    output['Id tâche'].append(f'DEB_{train[0]}_'+ creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Type de tâche'].append('DEB')
                    output['Jour'].append(creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Arr/Dep'].append(creneau_to_date(date0, creneau_arrivee[train]))
                    output['Heure début'].append(creneau_to_date(date0, c).strftime('%H:%M'))
                    output['Durée'].append(15)
                    output['Sillon'].append(train[0])
            
            # Tâches machines ur les trains du départ
            for train in trains_depart:
                if form[(train,c)].x==1:
                    output['Id tâche'].append(f'FOR_{train[0]}_'+ creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Type de tâche'].append('FOR')
                    output['Jour'].append(creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Arr/Dep'].append(creneau_to_date(date0, creneau_depart[train]))
                    output['Heure début'].append(creneau_to_date(date0, c).strftime('%H:%M'))
                    output['Durée'].append(15)
                    output['Sillon'].append(train[0])
                if deg[(train,c)].x==1:
                    output['Id tâche'].append(f'DEG_{train[0]}_' + creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Type de tâche'].append('DEG')
                    output['Jour'].append(creneau_to_date(date0, c).strftime('%d/%m/%Y'))
                    output['Arr/Dep'].append(creneau_to_date(date0, creneau_depart[train]))
                    output['Heure début'].append(creneau_to_date(date0, c).strftime('%H:%M'))
                    output['Durée'].append(15)
                    output['Sillon'].append(train[0])
        output["Occupation des voies par chantier (optim)"].append("Taux max d'occupation des voies (en %)")
        output["Occupation des voies par chantier (optim)"].append("Nombre max de voies occupées")
        output["Occupation des voies par chantier (optim)"].append("Nombre total de voies à disposition")
        while len(output["Occupation des voies par chantier (optim)"])!=len(output["Id tâche"]):
            output["Occupation des voies par chantier (optim)"].append(None)

        nb_voies={"WPY_REC": NVREC,
                    "WPY_FOR": NVFOR,
                    "WPY_DEP": NVDEP}
        for key in nb_voies:    
            output[key].append(100*max(nb_voie_occ[key])/nb_voies[key])
            output[key].append(max(nb_voie_occ[key]))
            output[key].append(nb_voies[key])
            while len(output[key])!=len(output["Id tâche"]):
                output[key].append(None)
        # Piping output into an excel sheet
        print(f"Résultats enregistrés dans le fichier {outputxlsx}")
        outputdf=pd.DataFrame(output)
        outputdf.to_excel(outputxlsx, index=False)

'''------------------------------- Vérification de la solution -------------------------------'''
# On a pu faire un script qui vérifie si les contraintes sont respectées
# Mais seulement dans le cas du Jalon 2
if SOLVED and JALON==2:
    print("Solution obtenue !")
    print('--------------------------------Vérification des contraintes--------------------')
    print('--------------------------------Trains d\'arrivée--------------------------------')
    verified=True
    for train in trains_arrivee:
        if verified==False:
            break
        debranchement=[]
        creneaux_occup_rec=[]
        for c in range(1,nombre_creneaux+1):
            if deb[(train,c)].x==1:
                debranchement.append(c)
            if orec[(train,c)].x==1:
                creneaux_occup_rec.append(c)
        for c in creneaux_occup_rec:
            if c in REC_INDIS:
                print("Contrainte Non respectée : Train occupe une voie pendant une indisponibilité")
                verified=False
                break
        if len(debranchement)!=1:
            print("Contrainte Non respectée : Train n'est pas débranché une seule fois")
            verified=False
            break
        for i in range(len(creneaux_occup_rec)-1):
            if creneaux_occup_rec[i+1]!=creneaux_occup_rec[i]+1:
                print("Contrainte Non respectée : Occupation du train non continue")
                verified=False
                break
        if creneaux_occup_rec[0]!=creneau_arrivee[train]:
            print("Contrainte Non respectée : Train n'occupe pas une voie à l'arrivée")
            verified=False
            break
        if creneaux_occup_rec[-1]!=debranchement[0]:
            print("Contrainte Non respectée : Train ne libère pas la voie après débranchement")
            verified=False
            break
        if debranchement[0]<=creneau_arrivee[train]+4:
            print("Contrainte Non respectée : Train débranché trop tôt")
            verified=False
            break
        if debranchement[0] in DEB_INDIS:
            print("Contrainte Non respectée : Train débranché pendant une indisponibilité")
            verified=False
            break
    for c in range(1,nombre_creneaux+1):
        if sum([deb[(i,c)].x for i in trains_arrivee])>1:
            print("Contrainte Non respectée : Plusieurs trains débranchés au même créneau")
            verified=False
            break
    if verified:
        print('Toutes les contraintes des trains d\'arrivée sont respectées')


    print('--------------------------------Trains du départ--------------------------------')
    for train in trains_depart:
        if verified==False:
            break
        # Créneau à partir duquel le train est censé de commencer
        # à occuper une voie dans le chantier de formation
        start_occ=nombre_creneaux+2 
        formation=[]
        degarage=[]
        creneaux_occup_for=[]
        creneaux_occup_dep=[]
        for c in range(1,nombre_creneaux+1):
            if form[(train,c)].x==1:
                formation.append(c)
            if deg[(train,c)].x==1:
                degarage.append(c)
            if oform[(train,c)].x==1:
                creneaux_occup_for.append(c)
            if odep[(train,c)].x==1:
                creneaux_occup_dep.append(c)
            for corr_train in At[train]:
                if deb[(corr_train,c)].x==1:
                    start_occ=min(start_occ,c)
        for c in creneaux_occup_for:
            if c in FOR_INDIS:
                print("Contrainte Non respectée : Train occupe une voie pendant une indisponibilité")
                verified=False
                break
        for c in creneaux_occup_dep:
            if c in DEP_INDIS:
                print("Contrainte Non respectée : Train occupe une voie pendant une indisponibilité")
                verified=False
                break 
        if len(formation)!=1:
            print("Contrainte Non respectée : Train n'était pas formé une seule fois")
            verified=False
            break
        if len(degarage)!=1:
            print("Contrainte Non respectée : Train n'était pas dégaré une seule fois")
            verified=False
            break
        for i in range(len(creneaux_occup_for)-1):
            if creneaux_occup_for[i+1]!=creneaux_occup_for[i]+1:
                print("Contrainte Non respectée : Occupation du train non continue")
                verified=False
                break
        for i in range(len(creneaux_occup_dep)-1):
            if creneaux_occup_dep[i+1]!=creneaux_occup_dep[i]+1:
                print("Contrainte Non respectée : Occupation du train non continue")
                verified=False
                break
        if creneaux_occup_for[0]!=start_occ:
            print("Contrainte Non respectée : Train n'occupe pas une voie au début de la formation")
            verified=False
            break
        if creneaux_occup_for[-1]!=degarage[0]:
            print("Contrainte Non respectée : Train ne libère pas la voie après dégarage")
            verified=False
            break
        if creneaux_occup_dep[0]!=degarage[0]:
            print("Contrainte Non respectée : Train ne libère pas la voie de formation après dégarage")
            verified=False
            break
        if creneaux_occup_dep[-1]!=creneau_depart[train]:
            print("Contrainte Non respectée : Train n'occupe pas une voie au départ")
            verified=False
            break
        if degarage[0]>=creneau_precis[train]:
            print("Contrainte Non respectée : Train dégaré trop tard")
            verified=False
            break
        if formation[0] in FOR_INDIS:
            print("Contrainte Non respectée : Train formé pendant une indisponibilité")
            verified=False
            break
        if degarage[0] in DEG_INDIS:
            print("Contrainte Non respectée : Train dégaré pendant une indisponibilité")
            verified=False
            break
    if verified:
        print('Toutes les contraintes des trains du départ sont respectées')

    print('--------------------------------Occupation des voies----------------------------') 
    if max(nb_voie_occ["WPY_REC"])>NVREC:
        print("Contrainte Non respectée : Occupation des voies du chantier de réception dépasse la capacité")
        verified=False
    if max(nb_voie_occ["WPY_FOR"])>NVFOR:
        print("Contrainte Non respectée : Occupation des voies du chantier de formation dépasse la capacité")
        verified=False
    if max(nb_voie_occ["WPY_DEP"])>NVDEP:
        print("Contrainte Non respectée : Occupation des voies du chantier de départ dépasse la capacité")
        verified=False
    if verified:
        print('Toutes les contraintes d\'occupation des voies sont respectées')






