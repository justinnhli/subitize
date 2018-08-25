/* globals $ */
"use strict";

$(function () {

    var PROPERTY_OPTION_MAP = [
        ["query", "#searchbar"],
        ["open", "#open"],
        ["semester", "#semesters-select"],
        ["instructor", "#instructors-select"],
        ["core", "#cores-select"],
        ["units", "#units-select"],
        ["department", "#departments-select"],
        ["lower", "#lower"],
        ["upper", "#upper"],
        ["day", "#days-select"],
        ["start_hour", "#start-hours-select"],
        ["end_hour", "#end-hours-select"]
    ];

    var option_defaults = null;
    var state = {
        search: {
        },
        gui: {
            show_options: false,
            tab: "search-results"
        },
        data: {
            saved_offerings: []
        }
    };
    var offering_data = {};

    // UTILITY

    function clone(obj) {
        return jQuery.extend(true, {}, obj);
    }

    // LOAD/SAVE PARAMETERS

    /* Get the hash of the URL
     * 
     * This function is necessary because location.hash is not always accurate.
     * In particular, when the back button is clicked, location.hash remains
     * empty even if the new URL has a hash. This function tries to use
     * location.hash first, but also tries to manually parse location if
     * location.hash is empty.
     */
    function get_url_hash() {
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
    }

    function load_state() {
        var hash = get_url_hash();
        if (hash !== "") {
            try {
                state = JSON.parse(decodeURI(hash));
            } catch (SyntaxError) {
            }
        }
        apply_state();
    }

    function apply_state() {
        show_tab(state.gui.tab);
        if (state.gui.show_options) {
            show_search_options();
        } else {
            hide_search_options();
        }
        for (var i = 0; i < PROPERTY_OPTION_MAP.length; i++) {
            var pair = PROPERTY_OPTION_MAP[i];
            var property = pair[0];
            var option = pair[1];
            if (state.search.hasOwnProperty(property)) {
                $(option).val(state.search[property]);
            } else {
                $(option).val(String(option_defaults[property]));
            }
        }
        if (state.search.query === undefined || state.search.query === "") {
            var searchbar = $("#searchbar");
            searchbar.val("search for courses...");
            searchbar.css("color", "#BABDB6");
        }
        if (Object.keys(state.search).length !== 0) {
            get_search_results();
        } else {
            clear_search_results();
        }
    }

    function save_state() {
        var url = location.origin + "#" + encodeURI(JSON.stringify(state));
        history.replaceState(state, "Subitize - Course Counts at a Glance", url);
        propagate_state();
    }

    function propagate_state() {
        $("a").each(function () {
            var a = $(this);
            if (!a.attr("href").startsWith("/")) {
                return;
            }
            a.change();
        });
    }

    // POPULATION SEARCH OPTIONS

    function load_option_defaults() {
        return $.get("defaults").done(function(response) {
            option_defaults = response;

            for (var i = 0; i < PROPERTY_OPTION_MAP.length; i++) {
                var pair = PROPERTY_OPTION_MAP[i];
                var property = pair[0];
                var option = $(pair[1]);
                if (option.attr("type") === "number") {
                    option_defaults[property] = parseInt(option_defaults[property]);
                }
            }
        });
    }

    function populate_select(field) {
        return $.get("/list?field=" + field).done(function(response) {
            var select = $("#" + field + "-select");
            for (var i = 0; i < response.length; i++) {
                var pair = response[i];
                var value = pair[0];
                var display_str = pair[1];
                select.append(
                    "<option value=\"" + value + "\">" + display_str + "</option>"
                );
            }
        });
    }

    // SHOW SEARCH RESULTS

    function clear_search_results() {
        $("#search-results-count").html(0);
        $("#search-results-table").empty();
    }

    function get_search_results() {
        show_tab("search-results");
        // clear search results
        clear_search_results()
        // add temporary loading message
        var search_results_header = build_course_listing_header("search-results");
        $("#search-results-table").append(search_results_header);
        search_results_header.after("<tbody class=\"search-results data\"><tr><td colspan=\"9\">Searching...</td></tr></tbody>");
        var parameters_str = [];
        for (var i = 0; i < PROPERTY_OPTION_MAP.length; i++) {
            var pair = PROPERTY_OPTION_MAP[i];
            var property = pair[0];
            var option = pair[1];
            if ($(option).val() !== option_defaults[property]) {
                parameters_str.push(property + "=" + $(option).val());
            }
        }
        var parameters = parameters_str.join("&");
        $.get("/json/?" + parameters).done(function(response) {
            // clear search results again
            clear_search_results();
            // repopulate search results
            $("#search-results-count").html(response.results.length);
            populate_search_results(response.metadata, response.results);
            enable_more_info_toggle();
        });

        return false;
    }

    function populate_search_results(metadata, results) {
        if (results.length === -1) {
            return;
        }
        $("#search-results-table").append(build_course_listing_header("search-results", metadata.sorted));
        var search_results_header = $("#search-results-header");
        for (var i = results.length - 1; i >= 0; i -= 1) {
            search_results_header.after(build_course_listing_row(results[i]));
        }
    }

    function link_updater(attrs, show_options) {
        return function () {
            var new_state = clone(state);
            new_state.search = {}
            for (var i = 0; i < attrs.length; i += 1) {
                new_state.search[attrs[i][0]] = attrs[i][1];
            }
            new_state.gui.show_options = show_options;
            $(this).attr("href", "/#" + encodeURI(JSON.stringify(new_state)));
        }
    }

    function build_course_listing_header(section, sort) {
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
            if (heading.hasOwnProperty("id") && sort) {
                html.push("<a href=\"/" + location.search + "&sort=" + heading.id + location.hash + "\">");
            }
            html.push(heading.label);
            if (heading.hasOwnProperty("id") && sort) {
                html.push("</a>");
                if (sort === heading.id) {
                    html.push(" &#9660; ");
                }
            }
        }
        html.push("</tr>");
        html.push("</tbody>");
        return $(html.join(""));
    }

    function build_course_listing_row(result, classnames) {
        var tbody = $("<tbody class=\"data\"></tbody>").append(tr);
        if (classnames === undefined) {
            tbody.addClass("search-results");
        } else {
            for (var i = 0; i < classnames.length; i += 1) {
                tbody.addClass(classnames[i]);
            }
        }
        tbody.addClass("data");
        var tr = $("<tr></tr>");
        tr.append(build_search_result_save_checkbox(result));
        tr.append(build_course_listing_semester_cell(result));
        tr.append(build_course_listing_course_cell(result));
        tr.append(build_course_listing_title_cell(result));
        tr.append(build_course_listing_units_cell(result));
        tr.append(build_course_listing_instructors_cell(result));
        tr.append(build_course_listing_meetings_cell(result));
        tr.append(build_course_listing_cores_cell(result));
        tr.append(build_course_listing_seats_cell(result));
        tbody.append(tr);
        if (result.info !== null) {
            tbody.append(build_search_result_info_row(result));
        }
        return tbody;
    }

    function build_search_result_save_checkbox(result) {
        var checkbox = $("<input type=\"checkbox\">");
        checkbox.addClass(result.id + "-checkbox");
        if (state.data.saved_offerings.includes(result.id)) {
            checkbox.prop("checked", "checked");
        }
        checkbox.click(function () {
            save_course_checkbox_handler(checkbox, result);
        });
        return checkbox;
    }

    function build_course_listing_semester_cell(result) {
        var link_text = result.semester.year + " " + result.semester.season;
        var td = $("<td></td>");
        var a = $("<a>" + link_text + "</a>").change(link_updater(
            [
                ["semester", result.semester.code]
            ],
            false
        ));
        a.change();
        td.append(a);
        return td;
    }

    function build_course_listing_course_cell(result) {
        var td = $("<td></td>");
        var link_text = "<abbr title=\"" + result.department.name + "\">" + result.department.code + "</abbr>";
        var a = $("<a>" + link_text + "</a>").change(link_updater(
            [
                ["semester", state.search.semester],
                ["department", result.department.code]
            ],
            true
        ));
        a.change()
        td.append(a);
        td.append(" ");
        link_text = result.number.string;
        a = $("<a>" + link_text + "</a>").change(link_updater(
            [
                ["semester", "any"],
                ["department", result.department.code],
                ["lower", result.number.number],
                ["upper", result.number.number]
            ],
            true
        ));
        a.change()
        td.append(a)
        td.append(" (" + result.section + ")");
        return td
    }

    function build_course_listing_title_cell(result) {
        var html = [];
        html.push("<td>");
        html.push(result.title);
        if (result.info) {
            html.push(" ");
            html.push("<span class=\"more-info\">[+]</span>");
        }
        html.push("</td>");
        return html.join("");
    }

    function build_course_listing_units_cell(result) {
        var html = [];
        html.push("<td>");
        html.push(result.units);
        html.push("</td>");
        return html.join("");
    }

    function build_course_listing_instructors_cell(result) {
        var td = $("<td></td>");
        if (result.instructors.length === 0) {
            td.append("Unassigned");
        } else {
            for (var i = 0; i < result.instructors.length; i += 1) {
                var instructor = result.instructors[i];
                var link_text = "<abbr title=\"" + instructor.system_name + "\">" + instructor.last_name + "</abbr>";
                var a = $("<a>" + link_text + "</a>").change(link_updater(
                    [
                        ["semester", state.search.semester],
                        ["instructor", instructor.system_name]
                    ],
                    true
                ));
                a.change();
                td.append(a);
                if (i < result.instructors.length - 1) {
                    td.append("; ");
                }
            }
        }
        return td;
    }

    function build_course_listing_meetings_cell(result) {
        var html = [];
        html.push("<td>");
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
        html.push("</td>");
        return html.join("");
    }

    function build_course_listing_cores_cell(result) {
        var td = $("<td></td>");
        for (var i = 0; i < result.cores.length; i += 1) {

            var core = result.cores[i];
            var link_text = "<abbr title=\"" + core.name + "\">" + core.code + "</abbr>";
            var a = $("<a>" + link_text + "</a>").change(link_updater(
                [
                    ["semester", state.search.semester],
                    ["core", core.code]
                ],
                true
            ));
            a.change();
            td.append(a);
            if (i < result.cores.length - 1) {
                td.append("; ");
            }
        }
        return td;
    }

    function build_course_listing_seats_cell(result) {
        var html = [];
        html.push("<td>");
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
        html.push("</abbr>");
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_info_row(result) {
        var html = [];
        html.push("<tr class=\"description\" style=\"display:none;\">");
        html.push("<td></td><td></td><td></td>");
        html.push("<td class=\"description\" colspan=\"3\">");
        if (result.info.description) {
            html.push(result.info.description);
        }
        if (result.info.prerequisites) {
            html.push("<p>Prerequisites: ");
            html.push(result.info.prerequisites);
            html.push("</p>");
        }
        if (result.info.corequisites) {
            html.push("<p>Corequisites: ");
            html.push(result.info.corequisites);
            html.push("</p>");
        }
        html.push("<p><a href=\"" + result.info.url + "\">View in Catalog</a></p>");
        html.push("</td>");
        html.push("<td></td><td></td><td></td>");
        html.push("</tr>");
        return html.join("");
    }

    // CHANGE GUI

    function show_search_options() {
        $(this).html("Hide Options");
        $("#advanced-search").show();
        state.gui.show_options = true;
    }

    function hide_search_options() {
        $(this).html("Show Options");
        $("#advanced-search").hide();
        state.gui.show_options = false;
    }

    // HANDLE GUI EVENTS

    function focus_searchbar() {
        var searchbar = $(this);
        if (searchbar.val() === "search for courses...") {
            searchbar.val("");
            searchbar.css("color", "#000000");
        }
    }

    function blur_searchbar() {
        var searchbar = $("#searchbar");
        if (searchbar.val() === "") {
            searchbar.val("search for courses...");
            searchbar.css("color", "#BABDB6");
        }
    }

    function submit_search(ev) {
        ev.preventDefault();
        state.search = {};
        for (var i = 0; i < PROPERTY_OPTION_MAP.length; i++) {
            var pair = PROPERTY_OPTION_MAP[i];
            var property = pair[0];
            var option = $(pair[1]);
            var value = option.val();
            if (option.attr("type") === "number") {
                value = parseInt(value);
            }
            if (value !== option_defaults[property]) {
                if (option.attr("type") === "checkbox") {
                    state.search[option.attr("name")] = option.is(":checked");
                } else {
                    state.search[option.attr("name")] = option.val();
                }
            }
        }
        var url = location.origin + "#" + encodeURI(JSON.stringify(state));
        window.location.replace(url);
    }

    function toggle_search_options() {
        if (state.gui.show_options) {
            hide_search_options();
        } else {
            show_search_options();
        }
        save_state();
    }

    function show_tab(tab) {
        $("#tab-list").show();
        $(".tab-heading").removeClass("active-tab");
        $(".tab-content").hide();
        $("#" + tab + "-heading").addClass("active-tab");
        $("#" + tab + "-content").show();
        state.gui.tab = tab;
    }

    function save_offering() {
    }

    function enable_more_info_toggle() {
        var more_info = $(".more-info");
        more_info.off("click").click(more_info_click_handler);
    }

    function more_info_click_handler() {
        var more_info = $(this);
        var desc_tr = more_info.parents("tbody").children(".description");
        var colspan = desc_tr.children(".description").attr("colspan");
        var tds = more_info.parents("td").prev("td").nextAll("td").slice(0, colspan);
        $.each(tds, function (i, td) {
            td = $(td);
            td.width(td.width());
        });
        desc_tr.toggle();
        if (desc_tr.is(":visible")) {
            more_info.html("[-]");
        } else {
            more_info.html("[+]");
        }
    }

    // MAIN

    function main() {

        show_tab(state.gui.tab);

        // set up GUI events
        $("#search-form").submit(submit_search);
        var searchbar = $("#searchbar");
        searchbar.focus(focus_searchbar);
        searchbar.blur(blur_searchbar);
        $("#options-toggle").click(toggle_search_options);
        $("#saved-courses-heading").click(function () {
            show_tab("saved-courses");
            save_state();
        });
        $("#search-results-heading").click(function () {
            show_tab("search-results");
            save_state();
        });

        // populate search options, then load state
        $.when(
            populate_select("semesters"),
            populate_select("instructors"),
            populate_select("cores"),
            populate_select("units"),
            populate_select("departments"),
            populate_select("days"),
            populate_select("start-hours"),
            populate_select("end-hours"),
            load_option_defaults()
        ).then(function () {
            load_state();
            save_state();
        });

        window.onpopstate = function (ev) {
            state = ev.state;
            load_state();
        };
    }

    main();

});
