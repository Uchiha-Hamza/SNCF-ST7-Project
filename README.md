# SNCF-ST7-Project
Optimisation des ressources en gare de triage pour FRET SNCF


## Modèle mathématique 
On a modélisé notre problème en partant du fait que les machines ne sont disponibles que pour un seul train et dans un seul créneau. \
De ce fait, on introduit les variables *binaires* suivantes : \
\
    - $(deb_{ic})$ : variable binaire indiquant si la machine de débranchement est utilisée \
    pour le sillion d'arrivée d'identifiant $i$ dans le créneau $c$ \
    - $(for_{ic})$ : variable binaire indiquant si la machine de formation est utilisée \
    pour le sillion du départ d'identifiant $i$ dans le créneau $c$ \
    - $(deg_{ic})$ : variable binaire indiquant si la machine de dégarage est utilisée \
    pour le sillion du départ d'identifiant $i$ dans le créneau $c$

Les créneaux ont une durée de $15 min$ correspondant à la durée d'une tâche machine. Les valeurs possibles des créneaux dépendent de l'instance, \
soit alors $c \in \{1,2,..., c_{max}\} $ où $c=1$ correspond au premier créneau de 15 min à parfir du premier jour de travail à $0:00$ et \
$c_{max}$ le dernier créneau du dernier jours de travail à partir de $23:45$.

On note ainsi : 
$$A = \{\text{Les identifiants des trains d'arrivée}\}$$
$$D = \{\text{Les identifiants des trains du départ}\}$$
$$C= \{1,2,..., c_{max}\}$$


## Contraintes
### 1. Unique débranchement, formation et dégarage
Chaque train d'arrivé subit un seul et unique débranchement, chaque train du départ subit un seul et unique débranchement et dégarage. 
$$ \forall i \in A \quad \sum_{c} deb_{i,c} = 1 $$
$$ \forall i \in D \quad \sum_{c} for_{i,c} = 1 $$
$$ \forall i \in D \quad \sum_{c} deg_{i,c} = 1 $$


### 2. Une seule tâche machine par créneau  
Chaque machine est exploitée par au plus un seul train sur chaque créneau.
$$ \forall c \in C \quad \sum_{i \in A} deb_{i,c} \leq 1 $$
$$ \forall c \in C \quad \sum_{i \in D} for_{i,c} \leq 1 $$
$$ \forall c \in C \quad \sum_{i \in D} deg_{i,c} \leq 1 $$


### 3. Débranchement se fait après l'arrivée du train
Pour chaque train d'arrivée $i$, le débranchement ne peut pas avoir lieu dans les créneaux précedent celui d'arrivée $c^{a}_{i}$ après une heure de tâches humaines.
$$ \forall i \in A \quad \sum_{c \space \leq \space c^{a}_{i}+4} deb_{i,c} = 0$$ 


### 4. Formation d'un train de départ 
Pour chaque train du départ $t$, la formation ne peut avoir lieu qu'après débranchement de tous les trains ayant les wagons qui le constituent. \
On note : $$ \forall t \in D \quad A_t = \{\text{Les identifiants des trains d'arrivée ayant au moins un wagon du train t}\}$$
On peut exprimer la contrainte comme suit : 
$$ \forall t \in D, \space\forall c \in C, \space\forall i \in A_t \quad for_{t,c} \leq \sum_{c' \space \lt \space c} deb_{i,c'}$$ 

### 5. Dégarage après formation
Pour chaque train du départ, le dégarage ne peut avoir lieu qu'après la formation du train et $150$ minutes soit $10$ créneaux de tâches humaines.
$$ \forall t \in D, \space\forall c \in C \quad deg_{t,c} \leq \sum_{c' \space \lt \space c-10} for_{t,c'}$$ 


### 6. Dégarage avant départ
Pour chaque train du départ $t$, le dégarage ne peut pas avoir lieu dans les créneaux suivants \
celui de $20$ minutes (de tâches humaines) avant le créneau du départ $c^{d}_{t}$.
$$ \forall t \in D \quad \sum_{c \space \geq \space c^{d}_{i}-2} deg_{i,c} = 0$$ 


### 7. Disponibilités des machines
Il y a des créneaux où les machines sont indisponible, soient alors  $ \space C_{deb}, C_{for}, C_{deg} \space$  ces crénaux d'indisponibilités.
$$ \forall i \in A \quad \sum_{c \space \in \space C_{deb}} deb_{i,c} = 0 $$
$$ \forall i \in D \quad \sum_{c \space \in \space C_{for}} for_{i,c} = 0 $$
$$ \forall i \in D \quad \sum_{c \space \in \space C_{deg}} deg_{i,c} = 0 $$
