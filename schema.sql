drop table if exists users;
    create table users (
    id integer primary key autoincrement,
    username text not null,
    password text not null,
    email text not null,
    realname text not null,
    born integer,
    gender text,
    parentid integer not null
);
