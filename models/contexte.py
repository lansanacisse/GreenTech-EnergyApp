import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
import requests


def contexte_page():
    st.header("Données")
    st.write(
        """
        Les données utilisées dans cette application sont des informations sur la performance énergétique 
        des logements en France. Les données sont collectées par le Ministère de la Transition Écologique et 
        Solidaire et sont disponibles sur le site data.gouv.fr.
    """
    )

    # Charger les données
    data = pd.read_csv("../data/sample_lon_lat.csv", sep=";")

    # Filtres
    st.sidebar.subheader("Filtres")

    # Choisir une variable à filtrer avec "Etiquette_DPE" comme valeur par défaut
    filter_variable = st.sidebar.selectbox(
        "Choisissez une variable pour filtrer les données:",
        data.columns,
        index=list(data.columns).index("Etiquette_DPE"),
    )

    # Créer dynamiquement des filtres basés sur les occurrences des valeurs de la variable choisie
    if filter_variable:
        unique_values = data[filter_variable].unique()
        selected_values = st.sidebar.multiselect(
            f"Choisissez les valeurs de {filter_variable}:",
            unique_values,
            default=unique_values[:3]
        )

    # Appliquer les filtres
    filtered_data = data
    if filter_variable and selected_values:
        filtered_data = filtered_data[
            filtered_data[filter_variable].isin(selected_values)
        ]


    
   # Sélection du nombre de lignes à afficher
    st.sidebar.subheader("Nombre de lignes à afficher")
    max_lines = len(filtered_data)
    num_lines = st.sidebar.slider(
        "Sélectionner le nombre de lignes à afficher:", 
        min_value=1, 
        max_value=max_lines, 
        value=min(100, max_lines)  # Définir la valeur par défaut à 100 ou au maximum de lignes disponibles
    )

    # Afficher un tableau filtré avec le nombre de lignes limité
    st.subheader("Tableau des Données Filtrées")
    st.write(filtered_data.head(num_lines))


    # Bouton de téléchargement CSV
    csv = filtered_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Télécharger les données en CSV",
        data=csv,
        file_name='donnees_filtres.csv',
        mime='text/csv',
    )


#################################APPEL API QUENTIN#################################
###################################################################################
###################################################################################

    # PARTIE API -> Il faut le excel adresse-69.csv pour lancer l'API
    # Bouton Lancer l'appel API à supprimer ? (met trop de temps à charger, l'utilisateur devrait déjà avoir les données)
    # Je n'ai garder que [["Date_réception_DPE", "Etiquette_DPE", "Code_postal_(BAN)", "Etiquette_GES", "Conso_5_usages/m²_é_finale", "Surface_habitable_logement"]] -> ajuster ?
    # Appel des données API ADEME et possibilité de rafraichir les données
    base_url_existant = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
    base_url_neuf = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-neufs/lines"

    # Chargement des codes postaux du département du Rhône (69)
    df_rhone = pd.read_csv("../data/adresses-69.csv", sep=";")
    liste_code_postal_rhone = sorted(df_rhone["code_postal"].unique().tolist())

    # Fonction pour appeler l'API
    ## @brief Fonction pour appeler l'API ADEME et récupérer les données de logements
    #  pour un département avant une certaine date.
    #  @param url L'URL de l'API ADEME pour les logements (existants ou neufs).
    #  @return Un DataFrame contenant les données récupérées de l'API.
    # On récupère les données pour chaque code postal du Rhône mais uniquement avant le 1er septembre 2024 (on va ensuite implémenter un bouton pour rafraichir les données)
    def call_API(url):
        all_results = []
        nb_ligne = 0
        liste_code_postal_rhone = sorted(df_rhone["code_postal"].unique().tolist())

        for code_postal in liste_code_postal_rhone:
            params = {
                "page": 1,
                "size": 10_000,
                "q": code_postal,
                "q_fields": "Code_postal_(BAN)",
                "qs": "Date_réception_DPE:[* TO 2023-09-01]"

            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                content = response.json()
                all_results.extend(content['results'])
                nb_ligne += content['total']
                
                if content['total'] > 10_000:
                    content = requests.get(content['next']).json()
                    all_results.extend(content['results'])
                    while 'next' in content:
                        content = requests.get(content['next']).json()
                        all_results.extend(content['results'])
            elif response.status_code == 204:
                st.write(f"Aucune donnée pour le code postal {code_postal}")
            elif response.status_code == 404:
                st.write(f"Ressource non trouvée pour le code postal {code_postal}.")
            elif response.status_code == 403:
                st.write(f"Accès refusé pour le code postal {code_postal}.")
            elif response.status_code == 500:
                st.write(f"Erreur interne du serveur pour le code postal {code_postal}.")
            elif response.status_code == 503:
                st.write(f"Service indisponible pour le code postal {code_postal}.")
            else:
                st.write(f"Erreur lors de la requête pour le code postal {code_postal}, code : {response.status_code}")

        df_complet = pd.DataFrame(all_results)
        # Sauvegarde des données dans un fichier CSV, on va plutôt créer un bouton pour télécharger les données
        # if url == base_url_existant:
        #     df_complet.to_csv("existant_69.csv", index=False)
        # elif url == base_url_neuf:
        #     df_complet.to_csv("neufs_69.csv", index=False)

        return df_complet

    ## @brief Fonction pour rafraîchir les données en récupérant les enregistrements
    #  de logements à partir du 2 septembre 2024.
    #  @param url L'URL de l'API ADEME pour les logements (existants ou neufs).
    #  @return Un DataFrame contenant les données mises à jour.
    def rafraichir_donnees(url):
        all_results = []
        nb_ligne = 0
        liste_code_postal_rhone = sorted(df_rhone["code_postal"].unique().tolist())

        for code_postal in liste_code_postal_rhone:
            params = {
                "page": 1,
                "size": 10_000,
                "q": code_postal,
                "q_fields": "Code_postal_(BAN)",
                "qs": "Date_réception_DPE:[2024-09-02 TO *]"
            }

            response = requests.get(url, params=params)
            if response.status_code == 200:
                content = response.json()
                all_results.extend(content['results'])
                nb_ligne += content['total']
                
                if content['total'] > 10_000:
                    content = requests.get(content['next']).json()
                    all_results.extend(content['results'])
                    while 'next' in content:
                        content = requests.get(content['next']).json()
                        all_results.extend(content['results'])
            elif response.status_code == 204:
                st.write(f"Aucune nouvelle donnée pour le code postal {code_postal}")
            elif response.status_code == 404:
                st.write(f"Ressource non trouvée pour le code postal {code_postal}.")
            elif response.status_code == 403:
                st.write(f"Accès refusé pour le code postal {code_postal}.")
            elif response.status_code == 500:
                st.write(f"Erreur interne du serveur pour le code postal {code_postal}.")
            elif response.status_code == 503:
                st.write(f"Service indisponible pour le code postal {code_postal}.")
            else:
                st.write(f"Erreur lors de la requête pour le code postal {code_postal}, code : {response.status_code}")

        df_complet = pd.DataFrame(all_results)
        # Sauvegarde des données dans un fichier CSV, on va plutôt créer un bouton pour télécharger les données
        # if url == base_url_existant:
        #     df_complet.to_csv("data/existant_69_refresh.csv", index=False)
        # elif url == base_url_neuf:
        #     df_complet.to_csv("data/neufs_69_refresh.csv", index=False)

        return df_complet

    # Interface Streamlit
    st.title("Application d'Appel API ADEME")

    st.write("Cliquez sur le bouton ci-dessous pour lancer l'appel API et extraire les données pour les logements existants et neufs dans le département du Rhône.")

    # Bouton pour lancer l'appel API
    if st.button("Lancer l'appel API"):
        with st.spinner("Appel de l'API en cours..."):
            # Appel API pour logements existants
            df_existants = call_API(base_url_existant)
            st.write("Données récupérées pour les logements existants :")
            st.dataframe(df_existants.head())

            # Appel API pour logements neufs
            df_neufs = call_API(base_url_neuf)
            st.write("Données récupérées pour les logements neufs :")
            st.dataframe(df_neufs.head())

            # Fusion des deux DataFrames
            common_columns = list(set(df_existants.columns).intersection(set(df_neufs.columns)))
            df_merged = pd.concat([df_existants[common_columns], df_neufs[common_columns]], ignore_index=True)
            df_merged.to_csv("../data/sample_lon_lat.csv", index=False, sep=';', encoding='utf-8-sig')
            st.write("Fusion des données terminée. Aperçu des données fusionnées :")
            st.dataframe(df_merged.head())

            st.success("L'appel API et la fusion des données ont été effectués avec succès.")

        st.write("Les fichiers CSV suivants ont été créés :")
        st.write("- `existant_69.csv` pour les logements existants")
        st.write("- `neufs_69.csv` pour les logements neufs")
        st.write("- `sample_lon_lat.csv` pour les données fusionnées")


    st.write("Les données à disposition ont pour étiquette DPE une date antérieur au 1er Septembre, lancer un nouvel appel API pour rafraîchir les données (après le 1er Septembre).")
    # Bouton pour rafraichir les données
    if st.button("Rafraichir les données (Après le 1er septembre 2024)"):
        
        df_merged = pd.read_csv("../data/sample_lon_lat.csv", sep=";")
        with st.spinner("Appel de l'API en cours..."):

            st.write("Cliquez sur le bouton ci-dessus pour lancer un nouvel appel API et extraire les données pour les logements existants et neufs dans le département du Rhône.")
            # On vérifie si le fichier existe déjà
            
            df_existants = rafraichir_donnees(base_url_existant)
            st.write("Extrait de données récupérées rafraichi pour les logements existants :")
            st.dataframe(df_existants[["Date_réception_DPE", "Etiquette_DPE", "Code_postal_(BAN)", "Etiquette_GES", "Conso_5_usages/m²_é_finale", "Surface_habitable_logement"]].sample(5))

            # Appel API pour logements neufs
            # On vérifie si le fichier existe déjà
            
            df_neufs = rafraichir_donnees(base_url_neuf)
            st.write("Extrait de données récupérées rafraichi pour les logements neufs :")
            st.dataframe(df_neufs[["Date_réception_DPE", "Etiquette_DPE", "Code_postal_(BAN)", "Etiquette_GES", "Conso_5_usages/m²_é_finale", "Surface_habitable_logement"]].sample(5))

            # Fusion des deux DataFrames
            common_columns = list(set(df_existants.columns).intersection(set(df_neufs.columns)))
            df_merged_refresh = pd.concat([df_existants[common_columns], df_neufs[common_columns]], ignore_index=True)
            df_merged.to_csv("data/merged_69_refresh.csv", index=False, sep=';', encoding='utf-8-sig')
            st.write("Fusion des données des logements avant le 1er septembre et après le 1er septembre terminée. Aperçu des données fusionnées :")
            st.dataframe(df_merged_refresh[["Date_réception_DPE", "Etiquette_DPE", "Code_postal_(BAN)", "Etiquette_GES", "Conso_5_usages/m²_é_finale", "Surface_habitable_logement"]].sample(5))
            st.success("Les données ont été mises à jour et combinées avec succès.")

            st.write("Les fichiers CSV suivants ont été créés :")
            st.write("- `existant_69_refresh.csv` pour les logements existants après le 1er septembre")
            st.write("- `neufs_69_refresh.csv` pour les logements neufs après le 1er septembre")

            st.success("L'appel API et la fusion des données ont été effectués avec succès.")

        # Option de téléchargement pour les CSV créés
        # st.download_button("Télécharger les données fusionnées", data=open("data/merged_69_combined.csv", "rb"), file_name="merged_69_combined.csv")

#################################FIN APPEL API QUENTIN#################################
###################################################################################
###################################################################################
