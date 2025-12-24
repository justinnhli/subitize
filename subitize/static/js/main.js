"use strict";

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const CALENDAR_SETTINGS = {
    "from_hour": 8,
    "upto_hour": 23,
    "five_minute_height": 5,
};

var curr_parameters = "";
var curr_tab = "";
var starred_courses_list = [];
var starred_courses = {};

/**
 * Link course numbers to a search for them.
 *
 * @param {Obj} result - The course object.
 * @param {string} text - The text to embed links in.
 * @returns {string} - The transformed text.
 */
const link_course_numbers = (result, text) => {
    var replacement = `<a href="/?advanced=true&semester=${document.getElementById("semester-select").value}&department=$1">`;
    if (result === null) {
        replacement += "$1";
    } else {
        replacement += `<abbr title="${result.department.name}">$1</abbr>`;
    }
    replacement += "</a>"
    replacement += " <a href=\"/?advanced=true&semester=any&department=$1&lower=$2&upper=$2\">$2</a>"
    return text.replace(/([A-Z]{3,4}) ([0-9]{1,3})/g, replacement);
};

/**
 * Handle the search.
 *
 * @returns {undefined}
 */
const search_handler = (event) => {
    event.preventDefault();
    const form_data = new FormData(document.getElementById("search-form"));
    const params = new URLSearchParams(form_data);
    search_from_parameters(params.toString(), true);
};

/**
 * Search from the given parameters.
 *
 * @param {string} parameters - The parameters from the search.
 * @param {boolean} update_history - Whether the history should be changed.
 * @returns {boolean} - Whether to change the URL.
 */
const search_from_parameters = (parameters, update_history) => {
    if (parameters === curr_parameters) {
        return;
    }
    show_tab("search-results");
    var search_results_table = document.getElementById("search-results-table");
    // clear search results
    search_results_table.innerHTML = "";
    // add temporary loading message
    var search_status_message = document.getElementById("search-status-message");
    search_status_message.innerHTML = "searching...";
    fetch("/simplify/?json=1&" + parameters)
    .then((response) => response.json())
    .then((response) => {
        // parse response
        var metadata = response.metadata;
        var results = response.results;
        // change url first so it can be used in links in the result
        curr_parameters = metadata.parameters;
        if (update_history) {
            save_starred_courses();
        }
        // update with search results, if any
        document.getElementById("search-results-count").innerHTML = results.length;
        if (results.length === 0) {
            // display a no results message
            search_status_message.innerHTML = "No Courses Found";
        } else {
            // remove temporary loading message
            search_status_message.innerHTML = "";
            // repopulate search results
            populate_search_results(metadata, results);
            // modify the new DOM as necessary
            enable_more_info_toggle();
            propagate_starred_courses();
        }
    });
};

/**
 * Populate the search results table.
 *
 * @param {Map<string, string>} metadata - The metadata about the results.
 * @param {List} results - The search results.
 * @returns {undefined}
 */
const populate_search_results = (metadata, results) => {
    if (results.length === 0) {
        return;
    }
    document.getElementById("search-results-table").appendChild(build_course_listing_header("search-results", metadata.sorted));
    var search_results_header = document.getElementById("search-results-header");
    for (var i = results.length - 1; i >= 0; i -= 1) {
        search_results_header.after(build_course_listing_row(results[i]));
    }
};

/**
 * Populate a course listing table header.
 *
 * @param {string} section - The section the table resides in.
 * @param {string} sort - The column to sort by.
 * @returns {Element} - The table header.
 */
const build_course_listing_header = (section, sort) => {
    // TODO keep heading, only change href and show sorted glyph
    var headings = [
        {label:""},
        {id:"semester", label:"Semester"},
        {id:"course", label:"Course (Section)"},
        {id:"title", label:"Title"},
        {id:"units", label:"Units"},
        {id:"instructors", label:"Instructors"},
        {id:"meetings", label:"Meeting Times (Room)"},
        {id:"cores", label:"Core"},
        {label:"Seats"}
    ];
    var html = [];
    html.push(`<tbody id="${section}-header" class="${section}">`);
    html.push("<tr>");
    for (var i = 0; i < headings.length; i += 1) {
        var heading = headings[i];
        html.push("<th>");
        if (Object.prototype.hasOwnProperty.call(heading, "id") && sort) {
            html.push(`<a href="${location.search}&sort=${heading.id}${location.hash}">`);
        }
        html.push(heading.label);
        if (Object.prototype.hasOwnProperty.call(heading, "id") && sort) {
            html.push("</a>");
            if (sort === heading.id) {
                html.push(" &#9660; ");
            }
        }
    }
    html.push("</tr>");
    html.push("</tbody>");
    const template = document.createElement("template");
    template.innerHTML = html.join("");
    return template.content.firstChild;
};

/**
 * Populate a course listing table row.
 *
 * @param {Obj} result - The course object.
 * @param {List<string>} classnames - CSS classes for the row.
 * @returns {JQuery} - The table header.
 */
const build_course_listing_row = (result, classnames) => {
    var tbody = document.createElement("tbody");
    tbody.classList.add("data");
    if (classnames === undefined) {
        tbody.classList.add("search-results");
    } else {
        for (var i = 0; i < classnames.length; i += 1) {
            tbody.classList.add(classnames[i]);
        }
    }
    var tr = document.createElement("tr");
    tr.appendChild(build_search_result_star_checkbox(result));
    tr.appendChild(build_course_listing_semester_cell(result));
    tr.appendChild(build_course_listing_course_cell(result));
    tr.appendChild(build_course_listing_title_cell(result));
    tr.appendChild(build_course_listing_units_cell(result));
    tr.appendChild(build_course_listing_instructors_cell(result));
    tr.appendChild(build_course_listing_meetings_cell(result));
    tr.appendChild(build_course_listing_cores_cell(result));
    tr.appendChild(build_course_listing_seats_cell(result));
    tbody.appendChild(tr);
    if (result.info !== null) {
        tbody.appendChild(build_search_result_info_row(result));
    }
    return tbody;
};

/**
 * Create a table cell to star an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_search_result_star_checkbox = (result) => {
    var td = document.createElement("td");
    td.className = "star-checkbox";
    var label = document.createElement("label");
    label.setAttribute("title", "star course");
    var checkbox = document.createElement("input");
    checkbox.setAttribute("type", "checkbox");
    checkbox.className = `offering_${result.id}-checkbox`;
    if (Object.prototype.hasOwnProperty.call(starred_courses, result.id)) {
        checkbox.checked = true;
    }
    checkbox.addEventListener("change", function(event) {
        star_course_checkbox_handler(event.target, result);
    });
    label.appendChild(checkbox);
    label.appendChild(document.createElement("span"));
    td.appendChild(label);
    return td;
};

/**
 * Create a table cell for the semester of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_semester_cell = (result) => {
    var td = document.createElement("td");
    td.innerHTML = `
        <a href="/?advanced=false&semester=${result.semester.code}">
            ${result.semester.year} ${result.semester.season}
        </a>
    `;
    return td;
};

/**
 * Create a table cell for the course number of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_course_cell = (result) => {
    var link = link_course_numbers(
        result,
        `${result.department.code} ${result.number.string}`,
    );
    var td = document.createElement("td");
    td.innerHTML = `${link} (${result.section})`;
    return td;
};

/**
 * Create a table cell for the title of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_title_cell = (result) => {
    var info = "";
    if (result.info) {
        info = "<span class=\"more-info\" title=\"show catalog info\">[+]</span>";
    }
    var td = document.createElement("td");
    td.innerHTML = `${result.title} ${info}`;
    return td;
};

/**
 * Create a table cell for the units of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_units_cell = (result) => {
    var td = document.createElement("td");
    td.innerHTML = result.units;
    return td;
};

/**
 * Create a table cell for the instructors of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_instructors_cell = (result) => {
    var html = [];
    if (result.instructors.length === 0) {
        html.push("Unassigned");
    } else {
        for (var i = 0; i < result.instructors.length; i += 1) {
            var instructor = result.instructors[i];
            html.push(`
                <a href="/?advanced=true&semester=${document.getElementById("semester-select").value}&instructor=${instructor.system_name}">
                      <abbr title="${instructor.system_name}">${instructor.last_name}</abbr>
                </a>
            `);
            if (i < result.instructors.length - 1) {
                html.push("; ");
            }
        }
    }
    var td = document.createElement("td");
    td.innerHTML = html.join("");
    return td;
};

/**
 * Create a table cell for the meeting times of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_meetings_cell = (result) => {
    var html = [];
    if (result.meetings.length === 0) {
        html.push("Time TBD (Location TBD)");
    } else {
        for (var i = 0; i < result.meetings.length; i += 1) {
            var meeting = result.meetings[i];
            if (meeting.weekdays === null) {
                html.push("Time TBD");
            } else {
                html.push(`
                    ${meeting.us_start_time} - ${meeting.us_end_time} 
                    <abbr title="${meeting.weekdays.names}">${meeting.weekdays.codes}</abbr>
                `);
            }
            if (i < result.meetings.length - 1) {
                html.push("; ");
            }
        }
    }
    var td = document.createElement("td");
    td.innerHTML = html.join("");
    return td;
};

/**
 * Create a table cell for the core requirements of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_cores_cell = (result) => {
    var html = [];
    var url = "";
    for (var i = 0; i < result.cores.length; i += 1) {
        var core = result.cores[i];
        var url = `/?advanced=true&semester=${document.getElementById("semester-select").value}&core=${core.code}`;
        html.push(`<a href="${url}"><abbr title="${core.name}">${core.code}</abbr></a>`);
        if (i < result.cores.length - 1) {
            html.push("; ");
        }
    }
    var td = document.createElement("td");
    td.innerHTML = html.join("");
    return td;
};

/**
 * Create a table cell for the number of seats of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_seats_cell = (result) => {
    var title = [];
    title.push(`Enrolled: ${result.num_enrolled}/${result.num_seats}`);
    if (result.num_reserved !== 0) {
        title.push(`Reserved Remaining: ${result.num_reserved_open}/${result.num_reserved}`);
    }
    title.push(`Waitlisted: ${result.num_waitlisted}`);
    var td = document.createElement("td");
    td.innerHTML = `
        <abbr title="${title.join("&#13;")}">
            ${result.num_enrolled}/${result.num_seats} [${result.num_waitlisted}]
        </abbr>
    `;
    return td;
};

/**
 * Create a table row for the catalog information of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table row.
 */
const build_search_result_info_row = (result) => {
    var html = [];
    html.push(`
        <td></td><td></td><td></td>
        <td class="description" colspan="3">
    `);
    if (result.info.description) {
        html.push(link_course_numbers(null, result.info.description));
    }
    if (result.info.prerequisites) {
        html.push(`<p>Prerequisites: ${link_course_numbers(null, result.info.prerequisites)}</p>`);
    }
    if (result.info.corequisites) {
        html.push(`<p>Corequisites: ${link_course_numbers(null, result.info.corequisites)}</p>`);
    }
    html.push(`
        <p><a href="${result.info.url}">View in Catalog</a></p>
        </td>
        <td></td><td></td><td></td>
    `);
    var tr = document.createElement("tr");
    tr.classList.add("description");
    tr.style.display = "none";
    tr.innerHTML = html.join("");
    return tr;
};

// starred courses tab

/**
 * Create the starred courses table.
 *
 * @returns {undefined}
 */
const build_starred_courses_table = () => {
    document.getElementById("starred-courses-table").appendChild(build_course_listing_header("starred-courses"));
    update_starred_courses_display();
};

const build_starred_courses_calendar = () => {
    const calendar = document.getElementById("starred-courses-calendar");
    // create column divs
    const row_header_div = document.createElement("div");
    row_header_div.classList.add("time-column");
    calendar.appendChild(row_header_div);
    const column_divs = WEEKDAYS.map((weekday, weekday_int) => {
        const column_div = document.createElement("div");
        column_div.classList.add("day-column");
        calendar.appendChild(column_div);
        return column_div;
    });
    // create hour row headers
    row_header_div.appendChild(document.createElement("div"));
    for (let hour = CALENDAR_SETTINGS.from_hour; hour < CALENDAR_SETTINGS.upto_hour; hour++) {
        const div = document.createElement("div");
        div.classList.add("header");
        if (hour == 12) {
            div.textContent = "NOON";
        } else {
            div.textContent = add_leading_zero(hour) + ":00";
        }
        row_header_div.appendChild(div);
    }
    // create weekday columns
    WEEKDAYS.entries().forEach(([weekday_int, weekday]) => {
        // create header
        const div = document.createElement("div");
        div.classList.add("header");
        div.textContent = weekday.toUpperCase();
        column_divs[weekday_int].appendChild(div);
        // create grid
        for (let hour = CALENDAR_SETTINGS.from_hour; hour < CALENDAR_SETTINGS.upto_hour; hour++) {
            const div = document.createElement("div");
            div.id = `calendar_grid_${weekday_int}_${add_leading_zero(hour)}`;
            div.classList.add("grid");
            column_divs[weekday_int].appendChild(div);
        }
    });
    update_starred_courses_display();
};

const add_leading_zero = ((value) =>
    value.toString().padStart(2, "0")
);


/**
 * Update the starred courses table.
 *
 * @returns {undefined}
 */
const update_starred_courses_display = () => {
    if (starred_courses_list.length !== Object.keys(starred_courses).length) {
        setTimeout(update_starred_courses_display, 200);
        return;
    }
    const starred_courses_table = document.getElementById("starred-courses-table");
    const starred_courses_header = document.getElementById("starred-courses-header");
    const calendar = document.getElementById("starred-courses-calendar");
    if (starred_courses_header) {
        if (starred_courses_list.length === 0) {
            starred_courses_header.style.display = "none";
            calendar.style.display = "none";
        } else {
            starred_courses_header.style.display = "";
            calendar.style.display = "";
        }
    }
    document.getElementById("starred-courses-count").innerHTML = starred_courses_list.length;
    starred_courses_list.sort();
    // clear starred courses table
    document.querySelectorAll("#starred-courses-table .data").forEach(e => e.remove());
    // clear checkboxes
    document.querySelectorAll("input[type=checkbox]").forEach(e => e.checked = false);
    // clear starred courses calendar
    document.querySelectorAll("#starred-courses-calendar .meeting").forEach(e => e.remove());
    // populate table
    const semesters = new Set();
    const borders = [];
    for (var i = starred_courses_list.length - 1; i >= 0; i -= 1) {
        // repopulate starred courses table
        var course = starred_courses[starred_courses_list[i]];
        var row = build_course_listing_row(course, ["starred-courses", `offering_${course.id}`]);
        starred_courses_table.appendChild(row);
        // recheck checkboxes
        document.querySelectorAll(`.offering_${course.id}-checkbox`).forEach(e => e.checked = true);
        // add to borders for calendar slots
        semesters.add(course.semester.code);
        course.meetings.entries().forEach(([schedule_index, schedule]) => {
            for (const weekday_int of schedule.weekdays.ints) {
                borders.push({
                    "course": course,
                    "schedule": schedule,
                    "schedule_index": schedule_index,
                    "weekday_int": weekday_int,
                    "time": schedule.start_minute,
                    "is_start": 1
                })
                borders.push({
                    "course": course,
                    "schedule": schedule,
                    "schedule_index": schedule_index,
                    "weekday_int": weekday_int,
                    "time": schedule.end_minute,
                    "is_start": 0
                })
            }
        });
    }
    // only update calendar if all courses in the same semester
    if (semesters.size !== 1) {
        calendar.style.display = "none";
        return;
    }
    // assign calendar slots
    const occupied_slots = new Set();
    const slots = {};
    const meetings = []
    let max_simultaneous = 0;
    sort_borders(borders).forEach((border) =>  {
        const meeting_id = `${border.course.id}_${border.schedule_index}`;
        if (border.is_start) {
            for (let i = 0; i < occupied_slots.size + 1; i++) {
                if (!occupied_slots.has(i)) {
                    occupied_slots.add(i);
                    border.slot = i;
                    meetings.push(border);
                    slots[meeting_id] = i;
                    break;
                }
            }
        } else {
            occupied_slots.delete(slots[meeting_id]);
        }
        if (occupied_slots.size > max_simultaneous) {
            max_simultaneous = occupied_slots.size;
        }
    });
    const course_width = 95 / max_simultaneous;
    // create calendar meetings
    meetings.forEach((meeting) => {
        const meeting_div = document.createElement("div");
        meeting_div.classList.add("meeting");
        meeting_div.classList.add(`meeting_${meeting.course.id}`);
        meeting_div.setAttribute("data-course", meeting.course.id);
        meeting_div.setAttribute("style", [
            `top:${100 * (meeting.time % 60) / 60}%`,
            `left:${meeting.slot * course_width}%`,
            `width:calc(${course_width}% - 3px)`,
            `height:${CALENDAR_SETTINGS.five_minute_height * (meeting.schedule.duration / 5)}px`,
        ].join("; "));
        const title = ([
            `${meeting.schedule.us_start_time}-${meeting.schedule.us_end_time}`,
            `${meeting.course.department.code} ${meeting.course.number.string}`,
            `${meeting.course.title}`,
        ].join("&#13;"));
        meeting_div.innerHTML = `<abbr title="${title}">${meeting.course.title}</abbr>`;
        const hour = add_leading_zero(parseInt(meeting.schedule.start_minute / 60));
        const grid = document.getElementById(`calendar_grid_${meeting.weekday_int}_${hour}`);
        meeting_div.addEventListener("mouseenter", calendar_mouse_enter_handler);
        meeting_div.addEventListener("mouseleave", calendar_mouse_leave_handler);
        grid.appendChild(meeting_div);
    });
};

const calendar_mouse_enter_handler = (event) => {
    const course_id = event.target.getAttribute("data-course");
    document.getElementById("starred-courses-calendar").querySelectorAll(`.meeting_${course_id}`).forEach(
        e => e.style.background = "#BABDB6"
    );
};

const calendar_mouse_leave_handler = (event) => {
    const course_id = event.target.getAttribute("data-course");
    document.getElementById("starred-courses-calendar").querySelectorAll(`.meeting_${course_id}`).forEach(
        e => e.style.background = "#EEEEEC"
    );
};


const sort_borders = ((borders) => {
    return borders.toSorted((a, b) => {
        if (a.weekday_int !== b.weekday_int) {
            return a.weekday_int - b.weekday_int;
        } else if (a.time !== b.time) {
            return a.time - b.time;
        } else if (a.is_start !== b.is_start) {
            return a.is_start - b.is_start;
        } else if (a.course.id < b.course.id) {
            return -1;
        } else if (b.course.id < a.course.id) {
            return 1;
        } else {
            return 0;
        };
    });
});


/**
 * Toggle saving and unsaving a course.
 *
 * @param {DOMObject} checkbox - The star course checkbox.
 * @param {Obj} result - The course object.
 * @returns {undefined}
 */
const star_course_checkbox_handler = (checkbox, result) => {
    if (checkbox.checked) {
        star_course(result);
    } else {
        unstar_course(result);
    }
    update_starred_courses_display();
    save_starred_courses();
    propagate_starred_courses();
    enable_more_info_toggle();
};

/**
 * Star a course.
 *
 * @param {Obj} result - The course object.
 * @returns {undefined}
 */
const star_course = (result) => {
    if (Object.prototype.hasOwnProperty.call(starred_courses, result.id)) {
        return;
    }
    starred_courses_list.push(result.id);
    starred_courses[result.id] = result;
    starred_courses_list.sort();
};

/**
 * Unstar a course.
 *
 * @param {Obj} result - The course object.
 * @returns {undefined}
 */
const unstar_course = (result) => {
    if (!Object.prototype.hasOwnProperty.call(starred_courses, result.id)) {
        return;
    }
    starred_courses_list.splice(starred_courses_list.indexOf(result.id), 1);
    delete starred_courses[result.id];
    document.querySelectorAll(`tbody.offering_${result.id}`).forEach(e => e.remove());
    document.querySelectorAll(`.offering_${result.id}-checkbox`).forEach(e => e.checked = false);
};

/**
 * Get the fragment/hash part of the URL.
 * 
 * This function is necessary because location.hash is not always accurate.
 * In particular, when the back button is clicked, location.hash remains
 * empty even if the new URL has a hash. This function tries to use
 * location.hash first, but also tries to manually parse location if
 * location.hash is empty.
 *
 * @returns {Obj} - The keys and values in the fragment.
 */
const get_url_hash = () => {
    var result = "";
    if (location.hash !== "") {
        result = location.hash.substring(1);
    } else {
        var parts = location.toString().split("#");
        if (parts.length > 1) {
            result = parts[parts.length - 1];
        }
    }
    return result;
};

/**
 * Load the starred courses from the URL.
 *
 * @returns {undefined}
 */
const load_starred_courses = () => {
    var course_list = get_url_hash();
    if (course_list === "") {
        starred_courses_list = [];
        starred_courses = {};
    } else {
        fetch(`/fetch/${course_list}`)
        .then((response) => response.json())
        .then((response) => {
            starred_courses_list = Object.keys(response);
            starred_courses_list.sort();
            starred_courses = response;
            update_starred_courses_display();
            save_starred_courses();
            if (curr_tab === "" && starred_courses_list.length > 0) {
                show_tab("starred-courses");
            }
        });
    }
};

/**
 * Save the starred courses into the URL.
 *
 * @returns {undefined}
 */
const save_starred_courses = () => {
    var url = location.origin;
    if (curr_parameters !== "") {
        url += `?${curr_parameters}`;
    }
    if (starred_courses_list.length > 0) {
        url += `#${starred_courses_list.join(",")}`;
    }
    history.pushState(null, "Subitize - Course Counts at a Glance", url);
};

/**
 * Update all links to contain the starred courses fragment.
 *
 * @returns {undefined}
 */
const propagate_starred_courses = () => {
    document.querySelectorAll("a").forEach(element => {
        var url = element.getAttribute("href");
        if (!url.startsWith("/")) {
            return;
        }
        var index = url.lastIndexOf("#");
        if (index !== -1) {
            url = url.substring(0, index);
        }
        if (starred_courses_list.length > 0) {
            url += `#${starred_courses_list.join(",")}`;
        }
        element.setAttribute("href", url);
    });
};

// Miscellaneous GUI

/**
 * Show a tab.
 *
 * @param {string} tab - The tab to show.
 * @returns {undefined}
 */
const show_tab = (tab) => {
    document.getElementById("tab-list").style.display = "block";
    if (curr_tab === "") {
        document.querySelectorAll(".tab").forEach(e => e.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(e => e.style.display = "none");
    } else {
        document.getElementById(`${curr_tab}-heading`).classList.remove("active");
        document.getElementById(`${curr_tab}-content`).style.display = "none";
    }
    document.getElementById(`${tab}-heading`).classList.add("active");
    document.getElementById(`${tab}-content`).style.display = "block";
    curr_tab = tab;
};

/**
 * Attach a handler to the catalog information toggle.
 *
 * @returns {undefined}
 */
const enable_more_info_toggle = () => {
    document.querySelectorAll(".more-info").forEach(element => {
        element.removeEventListener("click", more_info_click_handler);
        element.addEventListener("click", more_info_click_handler);
    });
};

/**
 * Clear the search bar when focused.
 *
 * @returns {undefined}
 */
const searchbar_focus_handler = (event) => {
    var searchbar = document.getElementById("searchbar");
    if (searchbar.value === "search for courses...") {
        searchbar.value = "";
        searchbar.style.color = "#000000";
    }
};

/**
 * Show default text in the search bar when unfocused.
 *
 * @returns {undefined}
 */
const searchbar_blur_handler = (event) => {
    var searchbar = document.getElementById("searchbar");
    if (searchbar.value === "") {
        searchbar.value = "search for courses...";
        searchbar.style.color = "#BABDB6";
    }
};

/**
 * Show/Hide the advanced search panel.
 *
 * @returns {undefined}
 */
const advanced_toggle_click_handler = (event) => {
    var toggle = document.getElementById("advanced-toggle");
    var state = document.getElementById("advanced-state");
    var div = document.getElementById("advanced-search");
    if (state.value.toLowerCase() === "true") {
        div.style.display = "none";
        toggle.innerHTML = "Show Options";
        state.value = "false";
    } else {
        div.style.display = "block";
        toggle.innerHTML = "Hide Options";
        state.value = "true";
    }
};

/**
 * Show/Hide catalog information.
 *
 * @returns {undefined}
 */
const more_info_click_handler = (event) => {
    const more_info = event.target;
    const orig_tr = more_info.closest("tr");
    const num_tds = orig_tr.children.length;
    const desc_tr = more_info.closest("tbody").querySelector(".description");
    var colspan = 0;
    var colspan_end_index = num_tds;
    for (var i = 0; i < num_tds; i++) {
        const orig_td = orig_tr.children[i];
        orig_td.style.maxWidth = `${orig_td.scrollWidth}px`;
        if (colspan !== 0 && i < colspan_end_index) {
            continue;
        }
        const desc_td = desc_tr.children[i - colspan];
        if (desc_td.getAttribute("colspan") !== null) {
            colspan = parseInt(desc_td.getAttribute("colspan")) - 1;
            colspan_end_index = i + colspan;
            desc_td.style.maxWidth = "0px";
        } else {
            desc_td.style.maxWidth = `${orig_td.scrollWidth}px`;
        }
    }
    if (desc_tr.style.display === "none") {
        desc_tr.style.display = "table-row";
        more_info.innerHTML = "[-]";
    } else {
        desc_tr.style.display = "none";
        more_info.innerHTML = "[+]";
    }
};

/**
 * Load the page.
 *
 * @param {boolean} from_back - Whether the page is loading from the
 *     navigating backwards.
 * @returns {undefined}
 */
const load_page = (from_back) => {
    // TODO set values of advanced options with javascript
    advanced_toggle_click_handler();
    advanced_toggle_click_handler();
    load_starred_courses();
    if (location.search) {
        search_from_parameters(location.search.substring(1), !from_back);
        show_tab("search-results");
    } else if (starred_courses_list.length > 0) {
        show_tab("starred-courses");
    }
    if (!from_back && !location.search) {
        save_starred_courses();
    }
    propagate_starred_courses();
};

/**
 * Set up the app.
 *
 * @returns {undefined}
 */
const main = () => {
    const searchbar = document.getElementById("searchbar");
    searchbar.addEventListener("focus", searchbar_focus_handler);
    searchbar.addEventListener("blur", searchbar_blur_handler);
    document.getElementById("search-form").addEventListener("submit", search_handler);
    document.getElementById("search-button").addEventListener("click", search_handler);
    document.getElementById("advanced-toggle").addEventListener("click", advanced_toggle_click_handler);
    document.getElementById("advanced-search").style.display = "none";
    document.getElementById("starred-courses-heading").addEventListener("click", () => {
        show_tab("starred-courses");
    });
    document.getElementById("search-results-heading").addEventListener("click", () => {
        show_tab("search-results");
    });
    window.addEventListener("popstate", () => {
        load_page(true);
    });
    build_starred_courses_table();
    build_starred_courses_calendar();
    load_page(false);
};
