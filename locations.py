# locations.py
# This file contains the database of States, Cities, and Areas.

INDIA_LOCATIONS = {
    "Andhra Pradesh": {
        "Vijayawada": ["Benz Circle", "PVP Mall", "Bus Stand", "Kanaka Durga Temple", "VR Siddhartha College", "Auto Nagar", "Patamata", "Gandhinagar", "Other"],
        "Visakhapatnam": ["RK Beach", "Jagadamba Junction", "GITAM University", "Rushikonda", "MVP Colony", "Gajuwaka", "Other"],
        "Guntur": ["Brundavan Gardens", "Vidyanagar", "Bus Station", "Amaravathi", "Other"],
        "Tirupati": ["Alipiri", "Renigunta", "SV University", "Tirumala", "Other"],
        "Kurnool": ["Konda Reddy Burru", "Nandyal Checkpost", "Other"],
        "Nellore": ["Trunk Road", "Magunta Layout", "Other"]
    },
    "Telangana": {
        "Hyderabad": ["Hitech City", "Gachibowli", "Jubilee Hills", "Banjara Hills", "Kukatpally", "Madhapur", "Secunderabad", "Charminar", "Other"],
        "Warangal": ["NIT Warangal", "Thousand Pillar Temple", "Hanamkonda", "Kazipet", "Other"],
        "Karimnagar": ["Bus Stand", "Mankammathota", "Other"]
    },
    "Karnataka": {
        "Bengaluru": ["Koramangala", "Indiranagar", "Whitefield", "Electronic City", "MG Road", "Jayanagar", "Marathahalli", "Majestic", "Other"],
        "Mysuru": ["Mysore Palace", "Gokulam", "VV Mohalla", "Other"],
        "Mangaluru": ["Panambur", "Hampankatta", "Other"]
    },
    "Maharashtra": {
        "Mumbai": ["Bandra", "Andheri", "Juhu", "Colaba", "Dadar", "Powai", "Goregaon", "Navi Mumbai", "Thane", "Other"],
        "Pune": ["Koregaon Park", "Hinjewadi", "Viman Nagar", "Kothrud", "Other"],
        "Nagpur": ["Sitabuldi", "Dharampeth", "Other"]
    },
    "Tamil Nadu": {
        "Chennai": ["T Nagar", "Adyar", "Velachery", "Anna Nagar", "Mylapore", "Guindy", "Marina Beach", "Other"],
        "Coimbatore": ["Gandhipuram", "RS Puram", "Peelamedu", "Other"],
        "Madurai": ["Meenakshi Temple Area", "Anna Nagar", "Other"]
    },
    "Delhi": {
        "New Delhi": ["Connaught Place", "Hauz Khas", "Saket", "Dwarka", "Karol Bagh", "Lajpat Nagar", "Nehru Place", "Vasant Kunj", "Chandni Chowk", "Other"]
    },
    "Uttar Pradesh": {
        "Lucknow": ["Hazratganj", "Gomti Nagar", "Aliganj", "Other"],
        "Noida": ["Sector 18", "Sector 62", "Botanical Garden", "Other"],
        "Varanasi": ["Assi Ghat", "BHU Campus", "Lanka", "Other"],
        "Kanpur": ["Mall Road", "Swaroop Nagar", "Other"]
    },
    "West Bengal": {
        "Kolkata": ["Park Street", "Salt Lake", "New Town", "Howrah", "Ballygunge", "Dum Dum", "Other"]
    },
    "Gujarat": {
        "Ahmedabad": ["Satellite", "Navrangpura", "Maninagar", "SG Highway", "Other"],
        "Surat": ["Vesu", "Adajan", "Varachha", "Other"]
    },
    "Rajasthan": {
        "Jaipur": ["Vaishali Nagar", "Malviya Nagar", "Raja Park", "Pink City", "Other"],
        "Udaipur": ["Fateh Sagar", "City Palace", "Other"]
    },
    "Kerala": {
        "Kochi": ["Fort Kochi", "Edappally", "MG Road", "Marine Drive", "Other"],
        "Thiruvananthapuram": ["Technopark", "Thampanoor", "Other"]
    },
    "Punjab": {
        "Chandigarh": ["Sector 17", "Sector 35", "Sukhna Lake", "Elante Mall", "Other"],
        "Ludhiana": ["Sarabha Nagar", "Model Town", "Other"],
        "Amritsar": ["Golden Temple Area", "Ranjit Avenue", "Other"]
    },
    # Generic fallback for places not listed above
    "Other States": {
        "Other City": ["Main Market", "Bus Stand", "Railway Station", "City Center", "Other"]
    }
}