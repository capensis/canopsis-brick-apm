# language : fr

Fonctionnalité: Recherche Google 
	Afin de tester la connexion internet nous faisons une recherche Google.

Scénario: 1. Atteindre Google - Test Erreur
	Soit l'utilisation d'un navigateur
	Quand j'atteins "http://www.google.fr"
	Alors le texte "Canopsis" apparait en moins de "2" secondes

Scénario: 2. Atteindre Google - Test Ok
	Soit l'utilisation d'un navigateur
	Quand j'atteins "http://www.google.fr"
	Alors le texte "Recherche" apparait en moins de "2" secondes

Scénario: 3. Recherchez Canopsis dans google - Test Ok
	Soit l'utilisation d'un navigateur
	Quand j'atteins "http://www.google.fr"
	Quand je saisis "Canopsis" dans le champ "q"
	Quand je clique sur le bouton "btnG"
	Alors je vois le texte "Canopsis"

Scénario: 4. Recherchez Canopsis dans google - Test Erreur
	Soit l'utilisation d'un navigateur1
	Quand j'atteins "http://www.google.fr"
	Quand je saisis "Canopsis" dans le champ "q"
	Quand je clique sur le bouton "btnG"
	Alors je vois le texte "DCNS"

