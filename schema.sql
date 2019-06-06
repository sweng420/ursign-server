drop table if exists users;
    create table users (
    id integer primary key autoincrement,
    username text not null,
    password text not null,
    email text not null,
    realname text not null,
    born integer,
    gender text,
    credits integer,
    balance integer,
    parentid integer not null -- a parent id > 0 means that it's a child account
);

drop table if exists collections;
create table collections (
       id integer primary key autoincrement,
       title text not null,
       xmldata text not null,
       prize int
);

-- table to associate collections with users (i.e to show who owns which collections)
drop table if exists collection_owners;
create table collection_owners (
       uid integer not null,
       cid integer not null,
       progress integer not null,
       foreign key(uid) references users(id),
       foreign key(cid) references collections(id)
);

drop table if exists quizzes;
create table quizzes (
       id integer primary key autoincrement,
       title text not null,
       xmldata text not null,
       prize int);

drop table if exists quiz_owners;
create table quiz_owners (
       uid integer not null,
       qid integer not null,
       progress integer not null,
       foreign key(uid) references users(id),
       foreign key(qid) references quizzes(id));

insert into users (username, password, email, realname, born, gender, balance, credits, parentid) values ('iyra', '$2b$12$FHffeKKEQNusvKMIfnWiI.pdKQGCeRVVUy91aFGOXItMecW6Yrzqu', 'isgb500@york.ac.uk', 'Iyra', 1996, 'male', 0, 0, 0); -- password is 'test'

insert into collections (title, xmldata, prize) values ('Sign Language Alphabet', '<some xml data>', 10);

insert into collections (title, xmldata, prize) values ('Common Phrases', '<other data>', 20);

insert into collection_owners (uid, cid, progress) values (1,1,0); -- iyra has the Alphabet collection
