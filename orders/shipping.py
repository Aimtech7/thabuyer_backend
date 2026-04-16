import easypost
from django.conf import settings

easypost.api_key = settings.EASYPOST_API_KEY

def create_address(structured_address):
    """
    structured_address: dict with street1, city, state, zip, country
    """
    try:
        return easypost.Address.create(
            street1=structured_address.get('street1'),
            street2=structured_address.get('street2', ''),
            city=structured_address.get('city'),
            state=structured_address.get('state'),
            zip=structured_address.get('zip_code'),
            country=structured_address.get('country', 'US'),
        )
    except Exception as e:
        # Fallback error handling in case of bad addresses or no token
        return None

def create_shipment(from_address_dict, to_address_dict, parcel_dict):
    """
    parcel_dict: dict with length, width, height, weight
    Returns list of rates
    """
    try:
        from_address = create_address(from_address_dict)
        to_address = create_address(to_address_dict)
        
        parcel = easypost.Parcel.create(
            length=parcel_dict.get('length', 10),
            width=parcel_dict.get('width', 10),
            height=parcel_dict.get('height', 10),
            weight=parcel_dict.get('weight', 16), # Default 1lb
        )
        
        shipment = easypost.Shipment.create(
            to_address=to_address,
            from_address=from_address,
            parcel=parcel
        )
        return shipment
    except Exception as e:
        return None

def buy_shipment(shipment_id, rate_id):
    """
    Buy a shipment label given an ID and rate ID.
    """
    try:
        shipment = easypost.Shipment.retrieve(shipment_id)
        shipment.buy(rate={'id': rate_id})
        return {
            'tracking_code': shipment.tracking_code,
            'carrier': shipment.selected_rate.carrier,
            'label_url': shipment.postage_label.label_url
        }
    except Exception as e:
        return None
