import os
import qrcode
import base64
from io import BytesIO
from datetime import date
from twilio.rest import Client
from django.conf import settings
from django.core.signing import TimestampSigner

signer = TimestampSigner()

def generate_pointing_qr(type_pointage):
    """
    Génère un QR code contenant une signature sécurisée pour le jour actuel.
    type_pointage: 'entree' ou 'sortie'
    """
    today = date.today().isoformat()
    data = f"pointage:{type_pointage}:{today}"
    
    # Signature pour éviter que quelqu'un crée son propre QR code
    signed_data = signer.sign(data)
    
    # Création du QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(signed_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Conversion en Base64 pour l'envoi facile au frontend
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def verify_qr_data(signed_data):
    """
    Vérifie la validité d'un QR code scanné.
    """
    try:
        # Vérifie la signature et que le code n'a pas plus de 12 heures (max_age en secondes)
        original_data = signer.unsign(signed_data, max_age=43200) 
        parts = original_data.split(':')
        if len(parts) == 3 and parts[0] == 'pointage':
            return {
                'type': parts[1],
                'date': parts[2]
            }
    except Exception:
        return None
    return None

def is_moroccan_holiday(dt: date):
    """
    Vérifie si une date donnée est un jour férié au Maroc.
    """
    fixed_holidays = [
        (1, 1), (1, 11), (5, 1), (7, 30), (8, 14), (8, 20), (8, 21), (11, 6), (11, 18),
    ]
    return (dt.month, dt.day) in fixed_holidays

def send_whatsapp_alert(to_phone, message):
    """
    Envoie une alerte WhatsApp réelle via Twilio.
    Le numéro 'to_phone' doit être au format '+212600000000'.
    """
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

    # Vérification des credentials
    if not account_sid or not auth_token or "votre_" in account_sid:
        print(f"--- SIMULATION WHATSAPP (Twilio non configuré) ---")
        print(f"To: {to_phone}")
        print(f"Message: {message}")
        print("-------------------------------------------------")
        return False

    try:
        client = Client(account_sid, auth_token)
        
        # Formatage du numéro de destination pour Twilio
        if not to_phone.startswith('whatsapp:'):
            # Si c'est un numéro pur, on ajoute le préfixe whatsapp:
            # On s'assure qu'il commence par +
            clean_phone = to_phone.strip()
            if not clean_phone.startswith('+'):
                clean_phone = '+' + clean_phone
            to_phone = f"whatsapp:{clean_phone}"

        message_sent = client.messages.create(
            body=message,
            from_=from_whatsapp_number,
            to=to_phone
        )
        print(f"WhatsApp alert sent successfully! SID: {message_sent.sid}")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp alert: {str(e)}")
        return False

def notify_rh_and_stagiaire(stagiaire, message):
    """
    Envoie une notification au stagiaire ET au RH.
    """
    rh_number = os.getenv('RH_WHATSAPP_NUMBER')
    
    # Notification Stagiaire
    if stagiaire.user.telephone_whatsapp:
        send_whatsapp_alert(stagiaire.user.telephone_whatsapp, message)
    
    # Notification RH
    if rh_number:
        send_whatsapp_alert(rh_number, f"[ALERT RH] {message}")
