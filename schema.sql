CREATE TABLE semesters (
	id INTEGER NOT NULL, 
	year INTEGER NOT NULL, 
	season VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT _year_season_uc UNIQUE (year, season)
);
CREATE TABLE timeslots (
	id INTEGER NOT NULL, 
	weekdays VARCHAR NOT NULL, 
	start TIME NOT NULL, 
	"end" TIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE buildings (
	id INTEGER NOT NULL, 
	code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_buildings_code ON buildings (code);
CREATE TABLE cores (
	id INTEGER NOT NULL, 
	code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_cores_code ON cores (code);
CREATE TABLE departments (
	id INTEGER NOT NULL, 
	code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_departments_code ON departments (code);
CREATE TABLE people (
	id INTEGER NOT NULL, 
	system_name VARCHAR, 
	first_name VARCHAR, 
	last_name VARCHAR, 
	nick_name VARCHAR, 
	PRIMARY KEY (id)
);
CREATE TABLE rooms (
	id INTEGER NOT NULL, 
	building_id INTEGER NOT NULL, 
	room VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT _building_room_uc UNIQUE (building_id, room), 
	FOREIGN KEY(building_id) REFERENCES buildings (id)
);
CREATE TABLE courses (
	id INTEGER NOT NULL, 
	department_id INTEGER NOT NULL, 
	number VARCHAR NOT NULL, 
	number_int INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT _department_number_uc UNIQUE (department_id, number), 
	FOREIGN KEY(department_id) REFERENCES departments (id)
);
CREATE TABLE meetings (
	id INTEGER NOT NULL, 
	timeslot_id INTEGER, 
	room_id INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(timeslot_id) REFERENCES timeslots (id), 
	FOREIGN KEY(room_id) REFERENCES rooms (id)
);
CREATE TABLE offerings (
	id INTEGER NOT NULL, 
	semester_id INTEGER NOT NULL, 
	course_id INTEGER NOT NULL, 
	section VARCHAR NOT NULL, 
	title VARCHAR NOT NULL, 
	units INTEGER NOT NULL, 
	num_enrolled INTEGER NOT NULL, 
	num_seats INTEGER NOT NULL, 
	num_reserved INTEGER NOT NULL, 
	num_reserved_open INTEGER NOT NULL, 
	num_waitlisted INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT _semester_course_section_uc UNIQUE (semester_id, course_id, section), 
	FOREIGN KEY(semester_id) REFERENCES semesters (id), 
	FOREIGN KEY(course_id) REFERENCES courses (id)
);
CREATE TABLE offering_meeting_assoc (
	id INTEGER NOT NULL, 
	offering_id INTEGER NOT NULL, 
	meeting_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offering_id) REFERENCES offerings (id) ON DELETE CASCADE, 
	FOREIGN KEY(meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
);
CREATE TABLE offering_core_assoc (
	id INTEGER NOT NULL, 
	offering_id INTEGER NOT NULL, 
	core_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offering_id) REFERENCES offerings (id) ON DELETE CASCADE, 
	FOREIGN KEY(core_id) REFERENCES cores (id) ON DELETE CASCADE
);
CREATE TABLE offering_instructor_assoc (
	id INTEGER NOT NULL, 
	offering_id INTEGER NOT NULL, 
	instructor_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offering_id) REFERENCES offerings (id) ON DELETE CASCADE, 
	FOREIGN KEY(instructor_id) REFERENCES people (id) ON DELETE CASCADE
);
