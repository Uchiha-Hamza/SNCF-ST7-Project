# SNCF-ST7-Project
Optimisation des ressources en gare de triage pour FRET SNCF

## Modèle mathématique 
Tout est détaillé dans ce [rapport](https://drive.google.com/file/d/1WFUsb0tvfwHvMy0uxGVrwjQ8EGRlRGkU/view?usp=sharing).

## Exécution
Pour optimizer une [instance] parmi MINI, SIMPLE, REALISTE ayant les contraintes du [jalon]  1, 2, 3
```bash
git clone https://github.com/Uchiha-Hamza/SNCF-ST7-Project.git
cd SNCF-ST7-Project/
python optimize.py [instance] [jalon]
```
Pour visuliser la solution en local http://127.0.0.1:5000 :
```bash
cd Visualisation
python display_gantt.py [instance] [jalon]
```

Exemple : 
```bash
git clone https://github.com/Uchiha-Hamza/SNCF-ST7-Project.git
cd SNCF-ST7-Project/
python optimize.py SIMPLE 2
cd Visualisation
python display_gantt.py SIMPLE 2
```

## Instance non résolues
L'optimisation de l'instance realiste en jalon 2 nous renvoie "Pas de solution". \
L'optimisation en jalon 3 nous renvoie "Pas de solution" pour toutes les instances.

