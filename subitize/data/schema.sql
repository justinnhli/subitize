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
	PRIMARY KEY (id), 
	CONSTRAINT _weekdays_time_uc UNIQUE (weekdays, start, "end")
);
CREATE TABLE buildings (
	code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (code)
);
CREATE TABLE cores (
	code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (code)
);
CREATE TABLE departments (
	code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	PRIMARY KEY (code)
);
CREATE TABLE people (
	id INTEGER NOT NULL, 
	system_name VARCHAR NOT NULL, 
	first_name VARCHAR NOT NULL, 
	last_name VARCHAR NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE rooms (
	id INTEGER NOT NULL, 
	building_code VARCHAR NOT NULL, 
	room VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT _building_room_uc UNIQUE (building_code, room), 
	FOREIGN KEY(building_code) REFERENCES buildings (code)
);
CREATE TABLE courses (
	id INTEGER NOT NULL, 
	department_code VARCHAR NOT NULL, 
	number VARCHAR NOT NULL, 
	number_int INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT _department_number_uc UNIQUE (department_code, number), 
	FOREIGN KEY(department_code) REFERENCES departments (code)
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
	core_code VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offering_id) REFERENCES offerings (id) ON DELETE CASCADE, 
	FOREIGN KEY(core_code) REFERENCES cores (code) ON DELETE CASCADE
);
CREATE TABLE offering_instructor_assoc (
	id INTEGER NOT NULL, 
	offering_id INTEGER NOT NULL, 
	instructor_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(offering_id) REFERENCES offerings (id) ON DELETE CASCADE, 
	FOREIGN KEY(instructor_id) REFERENCES people (id) ON DELETE CASCADE
);
CREATE TABLE course_descriptions (
	id INTEGER NOT NULL, 
	year INTEGER NOT NULL,
	course_id INTEGER NOT NULL,
	url VARCHAR NOT NULL,
	description VARCHAR,
	prerequisites VARCHAR,
	corequisites VARCHAR,
	parsed_prerequisites VARCHAR,
	PRIMARY KEY (id),
	CONSTRAINT _year_course_uc UNIQUE (year, course_id), 
	FOREIGN KEY(course_id) REFERENCES courses (id) ON DELETE CASCADE
);
CREATE INDEX ix_offering_meeting_assoc_offering_id ON offering_meeting_assoc (offering_id);
CREATE INDEX ix_offering_meeting_assoc_meeting_id ON offering_meeting_assoc (meeting_id);
CREATE INDEX ix_offering_core_assoc_core_code ON offering_core_assoc (core_code);
CREATE INDEX ix_offering_core_assoc_offering_id ON offering_core_assoc (offering_id);
CREATE INDEX ix_offering_instructor_assoc_offering_id ON offering_instructor_assoc (offering_id);
CREATE INDEX ix_offering_instructor_assoc_instructor_id ON offering_instructor_assoc (instructor_id);
