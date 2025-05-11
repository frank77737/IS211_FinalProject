# Franklyn Collaguazo | Project One Book Catalogue | IS211 Course Project

# Description 

A flask python based web appliation that helps users record details about the books they own. 
The application allows a user to login and type in an ISBN, which will instigate a 
search using the Google Books API. The server will save some of the information to a 
database, which will be used to show the user their list of books. 

###Sample ISBN numbers 
- 9780857197689
- 9781438236667
- 9780307453389
- 9781451648546

# To run the web app
```bash
python app.py
```

# To view the web app 

```
http://localhost:5000
```

## Usage

1. Register a new account or login with existing credentials
    - User Authencation 
2. On the dashboard, enter an ISBN number to search for a book
    - API call to search for a book
3. The book will be added to your collection if found
    - Enter data into Database
4. View your collection of books on the dashboard
    - GET data from database 
5. Delete books you no longer want to track
    - Delete and update changes in the database

# How it Works 
## User Authetnication and Session Manamgent 

The application uses Flask and SQLite to create a book tracking web app with secure user authentication. Users can register with a username and password, which are stored in an SQLite database. When logging in, credentials are checked, and a session is created using Flask’s session object to keep the user logged in across pages. A custom login_required decorator is used to restrict access to certain routes (like the dashboard) unless the user is authenticated. This promotes reusable and consistent access control throughout the app.

## Book Search and Integration with Google API 

A key feature of this app is its integration with the Google Books API. On the dashboard, users can search for books using an ISBN number. The app sends a request to the API using urllib.request.urlopen(), retrieves book information in JSON format, and extracts relevant fields like title, authors, page count, and average rating. Before saving the book, it checks if the same ISBN already exists for the user to avoid duplicates. Once verified, the book is saved in the user’s collection with the current date.


## Dashboard 

The dashboard displays all books associated with the logged-in user, sorted by the date they were added. Users can delete any book in their collection, but only if it belongs to their account—this is enforced by querying the books table with the user's ID and the book ID. Flash messages are used for clear feedback during login, registration, book addition, and deletion.


## Database 
  On app startup, the script checks and creates two tables if they don’t already exist: users and books. The users table stores login credentials, while the books table records information about each book a user adds, including a foreign key relationship that links each book to a user. This ensures that book data remains scoped to individual user accounts. Following a one to many relationship

## Databse Schema
1. users table:
   - id (Primary Key)
   - username (Unique)
   - password 

2. books table:
   - id (Primary Key)
   - isbn
   - title
   - author
   - page_count
   - rating
   - user_id (Foreign Key)
   - date_added