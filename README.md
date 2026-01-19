1. Descrierea generală a proiectului
Proiectul "Owen Wilson WOW" este o aplicație web de tip fan database dedicată centralizării tuturor momentelor în care actorul Owen Wilson folosește exclamația sa caracteristică ("Wow") în filme.
Aplicația oferă o interfață duală:
Partea publică: Permite utilizatorilor să vizualizeze o galerie de filme, să filtreze rezultatele după nume, an sau replică și să acceseze pagini de detaliu. Fiecare detaliu oferă acces la fișiere multimedia (audio, video în diverse rezoluții și imagini reprezentative).
Panoul de administrare (Admin Panel): O zonă securizată prin autentificare, unde administratorul poate gestiona baza de date. Funcționalitățile includ operațiuni de tip CRUD (Create, Read, Update, Delete): adăugarea de noi intrări "Wow", editarea metadatelor existente și ștergerea înregistrărilor.
De asemenea, aplicația expune un API REST (/api/wows), permițând integrarea datelor în alte aplicații externe.

2. Tehnologiile utilizate
Proiectul este construit folosind o arhitectură MVC (Model-View-Controller) adaptată pentru Flask.
Limbaj de programare: Python 3.
Framework Web: Flask - utilizat pentru rutare, gestionarea sesiunilor și randarea template-urilor.
Baza de date: MySQL - sistemul de gestiune a bazelor de date. Conectarea se realizează prin driverul pymysql.
ORM / Interacțiune DB: Flask-SQLAlchemy. Deși configurat ca ORM, proiectul utilizează preponderent interogări SQL Raw (db.text) pentru optimizarea citirii și scrierii datelor, demonstrând abilitatea de a manipula SQL direct.
Frontend:
HTML5 & Jinja2: Template engine-ul Flask pentru generarea dinamică a paginilor.
CSS / Bootstrap: Utilizat pentru design-ul responsive (grid system, card-uri, butoane, tabele), vizibil în clasele card, btn, table-striped.
Securitate:
Werkzeug Security: Pentru hash-uirea parolelor (generate_password_hash, check_password_hash).
Dotenv: Pentru gestionarea variabilelor de mediu sensibile (credențiale DB, chei secrete).

3. Structura datelor
Aplicația utilizează o abordare hibridă interesantă. Datele brute sunt stocate sub formă de JSON într-un tabel, dar interogările de citire se fac printr-un View SQL (v_wows) care structurează aceste date pentru a fi ușor de utilizat în interfață.
Principalele câmpuri ale setului de date (obiectul "Wow"):
id (Integer): Identificator unic al înregistrării (Primary Key).
movie (String): Titlul filmului în care apare exclamația.
year (Integer): Anul lansării filmului.
release_date (String): Data completă a lansării (ex: "2011-05-20").
director (String): Regizorul filmului.
character / role_name (String): Numele personajului interpretat de Owen Wilson.
timestamp (String): Minutul și secunda din film unde apare "Wow".
full_line (String): Replica completă (contextul dialogului).
current_wow_in_movie (Integer): Numărul curent al exclamației în filmul respectiv (ex: al 2-lea "Wow").
total_wows_in_movie (Integer): Numărul total de "Wow"-uri din acel film.
audio (String - URL): Link către fișierul audio al replicii.
video (Object/JSON): Un obiect ce conține link-uri pentru diverse rezoluții video (1080p, 720p, 480p).
image (String - Data URI): Imaginea scenei stocată direct ca text codificat în Base64 (data:image/...).
Tabela Users (pentru administrare):
Această tabelă este simplă și este folosită strict pentru autentificarea în panoul de admin.
id (Integer): Identificator unic.
username (String): Numele de utilizator (unic).
password_hash (String): Parola stocată criptat.

4. Utilizarea inteligenței artificiale
În cadrul acestui proiect, Inteligența Artificială (de exemplu, un asistent de tip LLM precum ChatGPT sau Gemini) a fost utilizată ca un "pair programmer" pentru a accelera dezvoltarea și a rezolva probleme tehnice specifice:
Generarea scheletului de cod (Boilerplate): AI-ul a ajutat la structurarea inițială a aplicației Flask, configurarea conexiunii la baza de date și crearea rutelor de bază.
Scrierea interogărilor SQL complexe: Funcția de filtrare și paginare (list_wows) necesită interogări SQL dinamice cu clauze WHERE variabile. AI-ul a fost utilizat pentru a scrie logica de concatenare a string-urilor SQL și pentru a asigura parametrizarea corectă (:movie, :year) pentru a preveni SQL Injection.
Depanare (Debugging): În momentele în care apăreau erori de tipul "Template Syntax Error" în Jinja2 sau erori de conexiune la baza de date, mesajele de eroare au fost analizate cu ajutorul AI pentru a identifica rapid cauza (de exemplu, gestionarea incorectă a tipurilor de date JSON).
Generarea CSS/Bootstrap: Pentru a obține un aspect vizual plăcut (cum ar fi cardurile din pagina principală), s-au cerut sugestii de clase Bootstrap standard pentru a aranja elementele în grid.

5. Concluzii
Concluzii personale: Realizarea proiectului "Owen Wilson WOW" a reprezentat o oportunitate excelentă de a înțelege ciclul complet de viață al unei aplicații web, de la baza de date până la interfața cu utilizatorul. Am învățat cum să interacționez cu o bază de date relațională folosind Python și cum să securizez accesul la anumite rute.
Dificultăți întâmpinate:
Manipularea JSON în SQL: O provocare majoră a fost gestionarea formatului JSON stocat în baza de date. Extragerea datelor pentru editare și salvarea lor înapoi a necesitat o atenție sporită la serializare (json.dumps) și deserializare (json.loads).
Validarea imaginilor: Gestionarea imaginilor ca string-uri Base64 (Data URI) a creat probleme inițiale legate de lungimea string-ului și validarea formatului corect în formularul de editare.
Soluții implementate:
Am implementat funcții helper precum form_to_obj și obj_to_form pentru a curăța și standardiza datele înainte de a ajunge în baza de date sau în formularul HTML.
Pentru securitate, am folosit un decorator personalizat @admin_required care verifică sesiunea utilizatorului înainte de a permite accesul la funcțiile administrative, protejând astfel baza de date de modificări neautorizate.
