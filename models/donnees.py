import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt
from utils import (
    save_fig_as_png,
    create_pie_chart,
    create_bar_chart,
    create_line_chart,
    create_histogram,
)


def donnees_page():
    st.header("Données")
    st.write(
        """
        Les données utilisées dans cette application sont des informations sur la performance énergétique 
        des logements en France. Les données sont collectées par le Ministère de la Transition Écologique et 
        Solidaire et sont disponibles sur le site data.gouv.fr.
    """
    )

    # Charger les données
    data = pd.read_csv("../data/merged_69_cleaned.csv")

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
            default=[unique_values[0]],
        )

    # Appliquer les filtres
    filtered_data = data
    if filter_variable and selected_values:
        filtered_data = filtered_data[
            filtered_data[filter_variable].isin(selected_values)
        ]

    # Afficher un tableau filtré
    st.subheader("Tableau des Données Filtrées")
    st.write(filtered_data)

    st.title("Visualisation des Données")

    # Choix du graphique
    st.sidebar.subheader("Choix du graphique")
    option = st.sidebar.selectbox(
        "Type de graphique:", ("Barres", "Camembert", "Lignes", "Histogramme")
    )

    # Affichage du graphique selon le choix de l'utilisateur
    if option == "Camembert":
        fig = create_pie_chart(
            filtered_data[filter_variable].value_counts().index,
            filtered_data[filter_variable].value_counts(),
        )
        st.pyplot(fig)
        if st.button("Télécharger le Camembert en PNG"):
            save_fig_as_png(fig, "camembert")

    elif option == "Barres":
        fig = create_bar_chart(
            filtered_data[filter_variable].value_counts().index,
            filtered_data[filter_variable].value_counts(),
        )
        st.pyplot(fig)
        if st.button("Télécharger les Barres en PNG"):
            save_fig_as_png(fig, "barres")

    elif option == "Lignes":
        fig = create_line_chart(
            filtered_data[filter_variable].value_counts().index,
            filtered_data[filter_variable].value_counts(),
        )
        st.pyplot(fig)
        if st.button("Télécharger les Lignes en PNG"):
            save_fig_as_png(fig, "lignes")

    elif option == "Histogramme":
        fig = create_histogram(
            filtered_data[filter_variable].value_counts(),
            filtered_data[filter_variable].value_counts().index,
        )
        st.pyplot(fig)
        if st.button("Télécharger l'Histogramme en PNG"):
            save_fig_as_png(fig, "histogramme")


# Données géographiques
def visualisation_geographique():
    st.sidebar.subheader("Carte géographique")

    # Charger les données
    data = pd.read_csv("../data/merged_69_cleaned.csv")

    # Vérifier que le fichier contient des colonnes latitude et longitude
    if "lat" in data.columns and "lon" in data.columns:
        st.subheader("Carte géographique des données")
        st.map(data[["lat", "lon"]])
    else:
        st.sidebar.error("Le fichier CSV doit contenir des colonnes 'lat' et 'lon'.")
