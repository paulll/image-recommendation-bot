# images = {id, score, rating, md5}
# image_tags = {imageid, tagname}
# image_likes = {imageid, userid}

create table images(id int primary key, score int, rating char(1), md5 char(32));
create table image_tags(imageid int, tagname text, primary key(imageid, tagname));
create table image_likes(imageid int, userid int, primary key(imageid, userid));

create index images_by_tag on image_tags using hash (tagname);
create index tags_by_image on image_tags using hash (imageid);
create index images_by_user on imake_likes using hash (userid);
create index image_users on imake_likes using hash (imageid);

# local
create table local_users(uid int primary key, last_post int);
create table local_likes(uid int, imageid int, primary key(uid, imageid));

create index local_images_by_user on local_likes using hash(uid);