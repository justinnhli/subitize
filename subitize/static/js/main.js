"use strict";

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
    var replacement = ""
    replacement += "<a href=\"/?advanced=true&semester=" + document.getElementById("semester-select").value + "&department=$1\">";
    if (result === null) {
        replacement += "$1";
    } else {
        replacement += "<abbr title=\"" + result.department.name + "\">$1</abbr>";
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
    var searching_message = document.createElement("p");
    searching_message.innerHTML = "searching...";
    search_results_table.after(searching_message);
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
        // remove temporary loading message
        searching_message.remove()
        // repopulate search results
        document.getElementById("search-results-count").innerHTML = results.length;
        populate_search_results(metadata, results);
        // modify the new DOM as necessary
        enable_more_info_toggle();
        propagate_starred_courses();
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
    html.push("<tbody id=\"" + section + "-header\" class=\"" + section + "\">");
    html.push("<tr>");
    for (var i = 0; i < headings.length; i += 1) {
        var heading = headings[i];
        html.push("<th>");
        if (Object.prototype.hasOwnProperty.call(heading, "id") && sort) {
            html.push("<a href=\"/" + location.search + "&sort=" + heading.id + location.hash + "\">");
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
    checkbox.className = "offering_" + result.id + "-checkbox";
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
    var html = [];
    var url = "";
    url = "/";
    url += "?advanced=false";
    url += "&semester=" + result.semester.code;
    html.push("<a href=\"" + url + "\">");
    html.push(result.semester.year + " " + result.semester.season);
    html.push("</a>");
    var td = document.createElement("td");
    td.innerHTML = html.join("");
    return td;
};

/**
 * Create a table cell for the course number of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_course_cell = (result) => {
    var html = [];
    var url = "";
    html.push(link_course_numbers(
        result,
        result.department.code + " " + result.number.string
    ));
    html.push(" ");
    html.push("(" + result.section + ")");
    var td = document.createElement("td");
    td.innerHTML = html.join("");
    return td;
};

/**
 * Create a table cell for the title of an offering.
 *
 * @param {Obj} result - The course object.
 * @returns {string} - The table cell.
 */
const build_course_listing_title_cell = (result) => {
    var html = [];
    html.push(result.title);
    if (result.info) {
        html.push(" ");
        html.push("<span class=\"more-info\" title=\"show catalog info\">[+]</span>");
    }
    var td = document.createElement("td");
    td.innerHTML = html.join("");
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
    var url = "";
    if (result.instructors.length === 0) {
        html.push("Unassigned");
    } else {
        for (var i = 0; i < result.instructors.length; i += 1) {
            var instructor = result.instructors[i];
            url = "/";
            url += "?advanced=true";
            url += "&semester=" + document.getElementById("semester-select").value;
            url += "&instructor=" + instructor.system_name;
            html.push("<a href=\"" + url + "\">");
            html.push("<abbr title=\"" + instructor.system_name + "\">");
            html.push(instructor.last_name);
            html.push("</abbr></a>");
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
                html.push(meeting.us_start_time);
                html.push("-");
                html.push(meeting.us_end_time);
                html.push(" ");
                html.push("<abbr title=\"" + meeting.weekdays.names + "\">");
                html.push(meeting.weekdays.codes);
                html.push("</abbr>");
            }
            if (result.semester.code >= "202001") {
                continue;
            }
            html.push(" (");
            if (meeting.building === null) {
                html.push("Location TBD");
            } else {
                html.push("<abbr title=\"" + meeting.building.name + "\">");
                html.push(meeting.building.code);
                html.push("</abbr>");
                html.push(" ");
                html.push(meeting.room);
            }
            html.push(")");
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
        url = "/";
        url += "?advanced=true";
        url += "&semester=" + document.getElementById("semester-select").value;
        url += "&core=" + core.code;
        html.push("<a href=\"" + url + "\">");
        html.push("<abbr title=\"" + core.name + "\">");
        html.push(core.code);
        html.push("</abbr></a>");
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
    var html = [];
    var title = [];
    title.push("Enrolled: " + result.num_enrolled + "/" + result.num_seats);
    title.push("&#13;");
    if (result.num_reserved !== 0) {
        title.push("Reserved Remaining: " + result.num_reserved_open + "/" + result.num_reserved);
        title.push("&#13;");
    }
    title.push("Waitlisted: " + result.num_waitlisted);
    html.push("<abbr title=\"" + title.join("") + "\">");
    html.push(result.num_enrolled + "/" + result.num_seats);
    html.push(" ");
    html.push("[" + result.num_waitlisted + "]");
    html.push("</abbr>");
    var td = document.createElement("td");
    td.innerHTML = html.join("");
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
    html.push("<td></td><td></td><td></td>");
    html.push("<td class=\"description\" colspan=\"3\">");
    if (result.info.description) {
        html.push(link_course_numbers(null, result.info.description));
    }
    if (result.info.prerequisites) {
        html.push("<p>Prerequisites: ");
        html.push(link_course_numbers(null, result.info.prerequisites));
        html.push("</p>");
    }
    if (result.info.corequisites) {
        html.push("<p>Corequisites: ");
        html.push(link_course_numbers(null, result.info.corequisites));
        html.push("</p>");
    }
    html.push("<p><a href=\"" + result.info.url + "\">View in Catalog</a></p>");
    html.push("</td>");
    html.push("<td></td><td></td><td></td>");
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
    if (starred_courses_header) {
        if (starred_courses_list.length === 0) {
            starred_courses_header.style.display = "none";
        } else {
            starred_courses_header.style.display = "";
        }
    }
    document.getElementById("starred-courses-count").innerHTML = starred_courses_list.length;
    starred_courses_list.sort();
    // clear starred courses table
    document.querySelectorAll("#starred-courses-table .data").forEach(e => e.remove());
    // clear checkboxes
    document.querySelectorAll("input[type=checkbox]").forEach(e => e.checked = false);
    var classes = ["starred-courses"];
    for (var i = starred_courses_list.length - 1; i >= 0; i -= 1) {
        // repopulate starred courses table
        var course = starred_courses[starred_courses_list[i]];
        var row = build_course_listing_row(course, classes.concat("offering_" + course.id));
        starred_courses_table.appendChild(row);
        // recheck checkboxes
        document.querySelectorAll(".offering_" + course.id + "-checkbox").forEach(e => e.checked = true);
    }
};

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
    document.querySelectorAll("tbody.offering_" + result.id).forEach(e => e.remove());
    document.querySelectorAll(".offering_" + result.id + "-checkbox").forEach(e => e.checked = false);
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
        fetch("/fetch/" + course_list)
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
        url += "?" + curr_parameters;
    }
    if (starred_courses_list.length > 0) {
        url += "#" + starred_courses_list.join(",");
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
            url += "#" + starred_courses_list.join(",");
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
        document.getElementById(curr_tab + "-heading").classList.remove("active");
        document.getElementById(curr_tab + "-content").style.display = "none";
    }
    document.getElementById(tab + "-heading").classList.add("active");
    document.getElementById(tab + "-content").style.display = "block";
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
        orig_td.style.maxWidth = orig_td.scrollWidth + "px";
        if (colspan !== 0 && i < colspan_end_index) {
            continue;
        }
        const desc_td = desc_tr.children[i - colspan];
        if (desc_td.getAttribute("colspan") !== null) {
            colspan = parseInt(desc_td.getAttribute("colspan")) - 1;
            colspan_end_index = i + colspan;
            desc_td.style.maxWidth = "0px";
        } else {
            desc_td.style.maxWidth = orig_td.scrollWidth + "px";
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
    load_page(false);
};
