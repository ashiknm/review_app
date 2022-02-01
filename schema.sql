create table if not EXISTS hotel(
    hotelid integer PRIMARY KEY AUTOINCREMENT,
    hotelname text NOT NULL,
    address text,
    overall_rating integer,
    weblink text,
    phone integer , 
    image_name text, 
    totalmenu integer, 
    totalworkers integer
);

create table users(
    userid integer PRIMARY KEY AUTOINCREMENT, 
    username text not null,
    password text not null, 
    admin integer default 0, 
    reviewed integer default 0
);

create table if not exists review(
    userid integer PRIMARY KEY AUTOINCREMENT, 
    username text,  
    rating integer, 
    review text not null,
    fake integer DEFAULT 0, 
    real integer default 0, 
    verified integer DEFAULT 0, 
    liked integer DEFAULT 0, 
    disliked integer default 0, 
    hotelid integer
);
