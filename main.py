from typing import List, Dict, Any, Union
import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from pymongo import MongoClient
import datetime as dt
from datetime import date
from pathlib import Path
import streamlit_authenticator as stauth
import phonenumbers
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from datetime import datetime
import pdfkit as pdf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def connect_to_mongodb() -> MongoClient:
    """
    Connects to MongoDB and returns the collection.

    Parameters:
    None

    Returns:
    pymongo.collection.Collection: The MongoDB collection.
    """
    
    username = st.secrets["MongoDB"]["mongo_username"]
    password = st.secrets["MongoDB"]["mongo_password"]
    cluster_url = st.secrets["MongoDB"]["mongo_cluster_url"]
    client = MongoClient(f"mongodb+srv://{username}:{password}@{cluster_url}/")
    db = client[st.secrets["MongoDB"]["DATABASE_NAME"]]
    collection = db[st.secrets["MongoDB"]["COLLECTION_NAME"]]
    #client.close()
    #client.close()
    return collection

def get_data() -> pd.DataFrame:
    """
    Retrieves data from MongoDB collection and converts it into a Pandas DataFrame.

    Parameters:
    None

    Returns:
    pandas.DataFrame: A DataFrame containing the data from the MongoDB collection.
    """
    
    collection = connect_to_mongodb()
    df = pd.DataFrame(list(collection.find()))
    return df

def ledenlijst_tonen(loggedin_user):
    """
    Shows the full member list based on the corresponding MongoDB collection

    Parameters:
    None

    Returns:
    None
    """

    ledenlijst = get_data()

    st.write("Aantal actuele leden: " + str(ledenlijst[ledenlijst['Actueel_lid'] == 'Ja'].shape[0]))

    st.dataframe(ledenlijst,
                 column_order=("ID","Partnerid","Aanspreekvorm","Naam","Voornaam","Straat","Postcode","Woonplaats","Landcode","Telefoon","GSM","Email","Geboortedatum","Enieuwsbrief","Nieuwbrief","Actueel_lid","Lidgeld","Begeleider"), 
                 column_config={
                     "ID": st.column_config.NumberColumn(
                         "Lid id",
                         format="%i"
                     ),
                     "Partnerid": st.column_config.NumberColumn(
                         "Partner ID",
                         format="%i"
                     ),
                     "Aanspreekvorm": st.column_config.TextColumn(
                         "Aanspreekvorm"
                     ),
                     "Naam":  st.column_config.TextColumn(
                         "Naam"
                     ),
                     "Voornaam":  st.column_config.TextColumn(
                         "Voornaam"
                     ),
                     "Straat":  st.column_config.TextColumn(
                         "Straat/huisnummer"
                     ),
                     "Postcode": st.column_config.NumberColumn(
                         "Postcode",
                         format="%i"
                     ),
                     "Woonplaats": st.column_config.TextColumn(
                         "Woonplaats"
                     ),
                     "Landcode": st.column_config.TextColumn(
                         "Landcode"
                     ),
                     "Telefoon": st.column_config.TextColumn(
                         "Telefoon"
                     ),
                     "GSM": st.column_config.TextColumn(
                         "GSM"
                     ),
                     "Email": st.column_config.TextColumn(
                         "Email"
                     ),
                     "Geboortedatum": st.column_config.DateColumn(
                         "Geboortedatum",
                         format="DD/MM/YYYY"
                     ),
                     "Enieuwsbrief": st.column_config.CheckboxColumn(
                         "E-nieuwsbrief"
                     ),
                     "Nieuwbrief": st.column_config.CheckboxColumn(
                         "Nieuwsbrief"
                     ),
                     "Actueel_lid": st.column_config.TextColumn(
                         "Actueel lid"
                     ),
                     "Lidgeld": st.column_config.CheckboxColumn(
                         "Lidgeld"
                     ),
                     "Begeleider": st.column_config.CheckboxColumn(
                         "Begeleider"
                     )

                 },
                 use_container_width=True, 
                 hide_index=True)
    
    if loggedin_user == "Administrator":
        if st.button("Jaarafsluiting"):
            if st.button("Annuleer"):
                st.warning("Jaarafsluiting geannuleerd.")
            if st.button("Bevestig"):
                try:
                    st.success("Jaarafsluiting uitgevoerd.")
                except:
                    st.error("Fout bij jaarafsluiting.")
                    
def nieuw_lid_ID() -> str:
    """
    Get the maximum value of the 'ID' field from the specified MongoDB collection and return this value + 1.

    Parameters:
    none

    Returns:
    - str: The maximum value of the 'ID' field + 1 
    """
    collection = connect_to_mongodb()
    current_max_id = collection.find_one(sort=[("ID", -1)], projection={"_id": 0, "ID": 1})["ID"]
    return str(int(current_max_id) + 1) if current_max_id else "1"

def format_phonenumber(phonenr, country):
    """
    Function to format a phonenumber

    Args:
        phonenr (_type_): _description_

    Returns:
        string: formatted phonenumber as string
    """

    if phonenr != "":
        phonenr_parsed = phonenumbers.parse(phonenr, country)
        return phonenumbers.format_number(phonenr_parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    else:
        return ""



def lid_toevoegen():
    """
    Adds a new member to the MongoDB collection based on inputvalues in a form.

    Parameters:
    None

    Returns:
    None
    """

    with st.form("Toevoegen", clear_on_submit=True):

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            id = st.text_input("Lid id", value=nieuw_lid_ID(), disabled=True)
            partnerid = st.text_input("Partner id") 
            aanspreekvorm = st.selectbox("Aanspreekvorm", ["Mijnheer", "Mevrouw"])
            naam = st.text_input("Naam")
            voornaam = st.text_input("Voornaam")
            straat = st.text_input("Straat en huisnummer")
            postcode = st.number_input("Postcode",format="%i",max_value=9999)
            woonplaats = st.text_input("Woonplaats")
            landcode = st.selectbox("Landcode", ["BE", "NL", "FR"], index=0)

        with col2:
            telefoon = st.text_input("Telefoon")
            gsm = st.text_input("GSM")
            email = st.text_input("Email")
            geboortedatum = st.date_input("Geboortedatum", min_value=dt.date(1900,1,1), format="DD/MM/YYYY")
            actueel_lid = st.selectbox("Actueel lid", ["Ja", "Nee", "Adres"])
            enieuwsbrief = st.checkbox("Enieuwsbrief")
            nieuwsbrief = st.checkbox("Nieuwsbrief")
            lidgeld = st.checkbox("Lidgeld")
            begeleider = st.checkbox("Begeleider")

        # Show the submit button and add the new member when pressed
        submitted = st.form_submit_button("Lid toevoegen")
        
        if submitted:

            # Create the new member dictionary to be passed to the insert statement
            nieuw_lid = {
                "ID": id,
                "Partnerid": partnerid,
                "Aanspreekvorm": aanspreekvorm,
                "Naam": naam,
                "Voornaam": voornaam,
                "Straat": straat,
                "Postcode": postcode,
                "Woonplaats": woonplaats,
                "Landcode": landcode,
                "Telefoon": format_phonenumber(telefoon, landcode),
                "Email": email,
                "Geboortedatum": dt.datetime.combine(geboortedatum, dt.time()),
                "Enieuwsbrief": enieuwsbrief,
                "Nieuwbrief": nieuwsbrief,
                "Actueel_lid": actueel_lid,
                "Lidgeld": lidgeld,
                "Begeleider": begeleider,
                "GSM": format_phonenumber(gsm, landcode)
                }

            try:
                # Add the new member to the collection
                collection = connect_to_mongodb()
                collection.insert_one(nieuw_lid)
                st.success(f"Lid met ID {id} is toegevoegd.")
            except:
                st.error(f"Lid met ID {id} kon niet toegevoegd worden.")



def lid_verwijderen():
    """
    Deletes a member from the MongoDB collection based on the selected value.

    Parameters:
    None

    Returns:
    None
    """

    # Get the members list
    ledenlijst = get_data()
    
    # Show a dropdown box with all the members
    dropboxlijst = (ledenlijst["ID"].astype(str) + " | " + ledenlijst["Naam"] + ", " + ledenlijst["Voornaam"]).sort_values().to_list()

    # Save the selected member into a variable
    geselecteerd_lid = st.selectbox("Te verwijderen lid", dropboxlijst)

    # Split the selected value to extract the ID
    selected_id = geselecteerd_lid.split(" | ")[0]

    # Show the action button with the delete action when pressed
    if st.button('Verwijder geselecteerd lid'):

        try:
            # Delete the record from the MongoDB collection
            collection = connect_to_mongodb()
            collection.delete_one({"ID": selected_id})
            st.success(f"Lid met ID {selected_id} is verwijderd.")
        except:
            st.error(f"Lid met ID {selected_id} kon niet verwijderd worden.")

def lid_aanpassen():
    """
    Function to update an existing member, to be selected via a dropdown box

    Parameters:
    None

    Returns:
    None
    """

    # Get the members list
    ledenlijst = get_data()

    # Show a dropdown box with all the members
    dropboxlijst = (ledenlijst["ID"].astype(str) + " | " + ledenlijst["Naam"] + ", " + ledenlijst["Voornaam"]).sort_values().to_list()

    # Save the selected member into a variable
    geselecteerd_lid = st.selectbox("Aan te passen lid", dropboxlijst)

     # Split the selected value to extract the ID
    selected_id = geselecteerd_lid.split(" | ")[0]

    # Get the selected member's information
    collection = connect_to_mongodb()
    member_data = collection.find_one({"ID": selected_id})

    # Show a form with the selected member's information so the user can update the necessary fields
    with st.form("Aanpassen", clear_on_submit=False):

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            id = st.text_input("Lid id", value=member_data.get("ID",""), disabled=True)
            partnerid = st.text_input("Partner id", value=member_data.get("Partnerid","")) 
            aanspreekvorm = st.selectbox("Aanspreekvorm", ["Mijnheer", "Mevrouw"], index=["Mijnheer", "Mevrouw"].index(member_data.get("Aanspreekvorm","")))
            naam = st.text_input("Naam", value=member_data.get("Naam",""))
            voornaam = st.text_input("Voornaam", value=member_data.get("Voornaam",""))
            straat = st.text_input("Straat en huisnummer", value=member_data.get("Straat",""))
            postcode = st.number_input("Postcode",value=member_data.get("Postcode",""))
            woonplaats = st.text_input("Woonplaats", value=member_data.get("Woonplaats",""))
            landcode = st.selectbox("Landcode", ["BE", "NL", "FR"], index=["BE", "NL", "FR"].index(member_data.get("Landcode","")))

        with col2:
            telefoon = st.text_input("Telefoon", value=member_data.get("Telefoon",""))
            gsm = st.text_input("GSM", value=member_data.get("GSM",""))
            email = st.text_input("Email", value=member_data.get("Email",""))
            geboortedatum = st.date_input("Geboortedatum", value=member_data.get("Geboortedatum",""), min_value=dt.date(1900,1,1), format="DD/MM/YYYY")
            actueel_lid = st.selectbox("Actueel lid", ["Ja", "Nee", "Adres"], index=["Ja", "Nee", "Adres"].index(member_data.get("Actueel_lid","Ja")))
            enieuwsbrief = st.checkbox("Enieuwsbrief", value=member_data.get("Enieuwsbrief",""))
            nieuwsbrief = st.checkbox("Nieuwsbrief", value=member_data.get("Nieuwsbrief",""))
            lidgeld = st.checkbox("Lidgeld", value=member_data.get("Lidgeld",""))
            begeleider = st.checkbox("Begeleider", value=member_data.get("Begeleider",""))

        # Show the submit button with the update action when pressed
        submitted = st.form_submit_button("Lid aanpassen")

        if submitted:

            # Create the edited member's dictionary to be passed to the update statement
            aangepast_lid = {
                # "ID": id,
                "Partnerid": partnerid,
                "Aanspreekvorm": aanspreekvorm,
                "Naam": naam,
                "Voornaam": voornaam,
                "Straat": straat,
                "Postcode": postcode,
                "Woonplaats": woonplaats,
                "Landcode": landcode,
                "Telefoon": format_phonenumber(telefoon, landcode),
                "Email": email,
                "Geboortedatum": dt.datetime.combine(geboortedatum, dt.time()),
                "Enieuwsbrief": enieuwsbrief,
                "Nieuwbrief": nieuwsbrief,
                "Actueel_lid": actueel_lid,
                "Lidgeld": lidgeld,
                "Begeleider": begeleider,
                "GSM": format_phonenumber(gsm, landcode)
                }
            
            try:
                collection.update_one({"ID": selected_id}, { "$set": aangepast_lid})
                st.success(f"Lid met ID {selected_id} is aangepast.")
            except:
                st.error(f"Lid met ID {selected_id} kon niet aangepast worden.")

def send_email(to_email: str, subject: str, message: str, attachment_path: str) -> None:
    """
    Send an email with an attachment.

    Parameters:
    - to_email (str): The recipient's email address.
    - subject (str): The subject of the email.
    - message (str): The body of the email.
    - attachment_path (str): The file path of the attachment.

    Returns:
    None
    """
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = 'pdemaers@gmail.com'
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach message
    msg.attach(MIMEText(message, 'plain'))

    # Attach file
    with open(attachment_path, 'rb') as file:
        part = MIMEApplication(file.read(), Name="attachment.pdf")
        part['Content-Disposition'] = f'attachment; filename="{attachment_path}"'
        msg.attach(part)

    # Connect to SMTP server and send the email
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'pdemaers@gmail.com'
    smtp_password = st.secrets["app_key"]["email_app_key"]

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg['From'], to_email, msg.as_string())


def nieuwsbrief_sturen() -> None:
    """
    Function to select and send the newsletter to all members for whom Enieuwsbrief is set to True

    Returns:
    None
    """
    st.title("Nieuwsbrief versturen")

    # Get the members list
    ledenlijst = get_data()

    # Filter DataFrame based on 'Enieuwsbrief' column
    email_lijst = ledenlijst[ledenlijst['Enieuwsbrief']]

    # Custom subject and body fields
    custom_subject = st.text_input("Onderwerp van het email bericht", "Onderwerp")
    custom_body = st.text_area("Tekst van het email bericht", "Tekst")

    # File upload
    file_uploaded = st.file_uploader("Kies het nieuwsbrief bestand", type=["pdf"])

    if file_uploaded:
        st.success("Nieuwsbrief bestand geselecteerd.")

        # Button to send email
        if st.button("Verstuur nieuwsbrief"):
            # Get file path
            file_path = "uploaded_file.pdf"
            with open(file_path, "wb") as file:
                file.write(file_uploaded.getvalue())

            # Send email for each selected address with custom subject and body
            for email in email_lijst["Email"]:
                send_email(email, custom_subject, custom_body, file_path)
                st.success(f"Email verstuurd naar {email} met nieuwsbrief.")


# ---------------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------------

# Set up the page
st.set_page_config(page_title="Kennisbeurs Druivenstreek", page_icon=":lightbulb:", layout="wide", initial_sidebar_state="expanded")

# Add a title to the page
st.title("Kennisbeurs Druivenstreek - Ledenlijst")

# User authentication

usernames = st.secrets["Users"]["usernames"]
names = st.secrets["Users"]["names"]
passwords = st.secrets["Users"]["passwords"]
hashed_passwords = stauth.Hasher(passwords).generate()

credentials = {"usernames":{}}

for username, name, hashed_password in zip(usernames, names, hashed_passwords):
    user_dict = {"name":name,"password":hashed_password}
    credentials["usernames"].update({username:user_dict})

if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None

authenticator = stauth.Authenticate(credentials, "kb_ledenlijst", "abcdef", cookie_expiry_days=0)

name, authentication_status, username = authenticator.login("Login", "main")

if st.session_state["authentication_status"] == False:
    st.error("Username/password is incorrect.")

if st.session_state["authentication_status"] == None:
    st.warning("Please enter your username and password.")

if st.session_state["authentication_status"]:

    if name == "Administrator":
        menu_options = ["Ledenlijst", "Lid Toevoegen", "Lid Verwijderen", "Lid Aanpassen","Nieuwsbrief"]
        menu_icons = ["table", "person-fill-add", "person-fill-dash", "person-fill-gear","envelope-at"]
    elif name == "Bestuur":
        menu_options = ["Ledenlijst"]
        menu_icons = ["table"]

    # Set up the main options menu
    with st.sidebar:
        
        authenticator.logout("Logout", "sidebar")
        st.write(f"Ingelogd als: *{name}*")

        selected = option_menu(
            menu_title = "Menu",
            options = menu_options,
            icons = menu_icons,
            menu_icon="cast"
        )

    # Execute the appropriate function based on the selected option menu
    if selected == 'Ledenlijst':
        ledenlijst_tonen(name)
    elif selected == 'Lid Toevoegen':
        lid_toevoegen()
    elif selected == "Lid Verwijderen":
        lid_verwijderen()
    elif selected == "Lid Aanpassen":
        lid_aanpassen()
    elif selected == "Nieuwsbrief":
        nieuwsbrief_sturen()
