from pymongo import MongoClient

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['aek_noc']

    # Check applications
    apps = list(db.applications.find({}, {'_id': 1, 'business_name': 1, 'certificate_number': 1}).limit(5))
    print("Applications:")
    for app in apps:
        print(f"ID: {app['_id']}, Business: {app.get('business_name', 'N/A')}, Cert: {app.get('certificate_number', 'N/A')}")

    # Check certificates
    certs = list(db.certificates.find({}, {'_id': 1, 'certificate_number': 1, 'business_name': 1}).limit(5))
    print("\nCertificates:")
    for cert in certs:
        print(f"ID: {cert['_id']}, Cert Number: {cert.get('certificate_number', 'N/A')}, Business: {cert.get('business_name', 'N/A')}")

except Exception as e:
    print(f"Error: {e}")
