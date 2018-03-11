"use strict";

$(function () {

    function search_handler() {
        search_from_parameters($("#search-form").serialize());
        // return false to prevent the URL changing
        return false;
    }

    function search_from_parameters(parameters) {
        $.get("/simplify?json=1&" + parameters).done(function(response) {
            // parse response
            var metadata = response.metadata;
            var results = response.results;
            // change url first so it can be used in links in the result
            history.pushState(null, "Subitize - Course Counts at a Glance", window.location.origin + "?" + metadata.parameters);
            // clear previous search results
            var results_div = $("#results");
            results_div.empty();
            // repopulate search results
            if (results.length === 0) {
                results_div.append("<h3>No courses found.</h3>");
            } else {
                populate_search_results(metadata, results);
            }
        });
    }

    function populate_search_results(metadata, results) {
        var results_table = $("<table></table>");
        results_table.attr("id", "results-table");
        results_table.append(build_search_results_header(metadata.sorted));
        for (var i = 0; i < results.length; i += 1) {
            results_table.append(build_search_result_row(metadata, results[i]));
        }
        $("#results").append(results_table);
    }

    function build_search_results_header(sort) {
        var headings = [
            {id:"semester", label:"Semester"},
            {id:"course", label:"Course (Section)"},
            {id:"title", label:"Title"},
            {id:"units", label:"Units"},
            {id:"instructors", label:"Instructors"},
            {id:"meetings", label:"Meeting Times (Room)"},
            {id:"cores", label:"Core"},
            {id:"seats", label:"Seats"}
        ];
        var html = [];
        html.push("<thead>");
        html.push("<tr>");
        for (var i = 0; i < headings.length; i += 1) {
            var heading = headings[i];
            html.push("<th><a href=\"" + window.location + "&sort=" + heading.id + "\">" + heading.label + "</a>");
            if (sort === heading.id) {
                html.push(" &#9660; ");
            }
        }
        html.push("</tr>");
        html.push("</thead>");
        return html.join("");
    }

    function build_search_result_row(metadata, result) {
        var html = [];
        html.push("<tbody>");
        html.push("<tr>");
        html.push(build_search_result_semester_cell(metadata, result));
        html.push(build_search_result_course_cell(metadata, result));
        html.push(build_search_result_title_cell(metadata, result));
        html.push(build_search_result_units_cell(metadata, result));
        html.push(build_search_result_instructors_cell(metadata, result));
        html.push(build_search_result_meetings_cell(metadata, result));
        html.push(build_search_result_cores_cell(metadata, result));
        html.push(build_search_result_seats_cell(metadata, result));
        html.push("</tr>");
        html.push("</tbody>");
        return html.join("");
    }

    function build_search_result_semester_cell(metadata, result) {
        var html = [];
        var url = "";
        html.push("<td>");
        url = window.location.origin;
        url += "?advanced=" + metadata.advanced;
        url += "&semester=" + result.semester.code;
        html.push("<a href=\"" + url + "\">");
        html.push(result.semester.year + " " + result.semester.season);
        html.push("</a>");
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_course_cell(metadata, result) {
        var html = [];
        var url = "";
        html.push("<td>");
        url = window.location.origin;
        url += "?advanced=true";
        url += "&department=" + result.department.code;
        html.push("<a href=\"" + url + "\">");
        html.push("<abbr title=\"" + result.department.name + "\">");
        html.push(result.department.code);
        html.push("</abbr></a>");
        html.push(" ");
        url += "&semester=any";
        url += "&lower=" + result.number.number;
        url += "&upper=" + result.number.number;
        html.push("<a href=\"" + url + "\">");
        html.push(result.number.string);
        html.push("</a>");
        html.push(" ");
        html.push("(" + result.section + ")");
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_title_cell(metadata, result) {
        var html = [];
        html.push("<td>");
        html.push(result.title);
        if (result.has_info) {
            html.push(" ");
            html.push("<span class=\"more-info\">[+]</span>");
        }
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_units_cell(metadata, result) {
        var html = [];
        html.push("<td>");
        html.push(result.units);
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_instructors_cell(metadata, result) {
        var html = [];
        var url = "";
        html.push("<td>");
        if (result.instructors.length === 0) {
            html.push("Unassigned");
        } else {
            for (var i = 0; i < result.instructors.length; i += 1) {
                var instructor = result.instructors[i];
                url = window.location.origin;
                url += "?advanced=true";
                url += "&semester=" + result.semester.code;
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
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_meetings_cell(metadata, result) {
        var html = [];
        html.push("<td>");
        if (result.meetings.length === 0) {
            html.push("Time TBD (Location TBD)");
        } else {
            for (var i = 0; i < result.meetings.length; i += 1) {
                var meeting = result.meetings[i];
                if (!meeting.hasOwnProperty("weekdays")) {
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
                if (!meeting.hasOwnProperty("room")) {
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

    function build_search_result_cores_cell(metadata, result) {
        var html = [];
        var url = "";
        html.push("<td>");
        for (var i = 0; i < result.cores.length; i += 1) {
            var core = result.cores[i];
            url = window.location.origin;
            url += "?advanced=true";
            url += "&semester=" + result.semester.code;
            url += "&core=" + core.coe;
            html.push("<a href=\"" + url + "\">");
            html.push("<abbr title=\"" + core.name + "\">");
            html.push(core.code);
            html.push("</abbr></a>");
            if (i < result.cores.length - 1) {
                html.push("; ");
            }
        }
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_seats_cell(metadata, result) {
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
        html.push(" ");
        html.push("[" + result.num_waitlisted + "]");
        html.push("</abbr>");
        html.push("</td>");
        return html.join("");
    }

    function searchbar_focus_handler() {
        var searchbar = $(this);
        if (searchbar.val() === "search for courses...") {
            searchbar.val("");
            searchbar.css("color", "#000000");
        }
    }

    function searchbar_blur_handler() {
        var searchbar = $("#searchbar");
        if (searchbar.val() === "") {
            searchbar.val("search for courses...");
            searchbar.css("color", "#BABDB6");
        }
    }

    function advanced_toggle_click_handler() {
        var toggle = $(this);
        var state = $("#advanced-state");
        var div = $("#advanced-search");
        if (state.val().toLowerCase() === "true") {
            div.css("display", "none");
            toggle.html("Show Options");
            state.val("false");
        } else {
            div.css("display", "block");
            toggle.html("Hide Options");
            state.val("true");
        }
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

    function main() {
        var search_form = $("#search-form");
        search_form.submit(search_handler);

        var searchbar = $("#searchbar");
        searchbar.focus(searchbar_focus_handler);
        searchbar.blur(searchbar_blur_handler);

        var search_button = $("#search-button");
        search_button.click(search_handler);

        var advanced_toggle = $("#advanced-toggle");
        advanced_toggle.click(advanced_toggle_click_handler);

        var more_info = $(".more-info");
        more_info.click(more_info_click_handler);

        // TODO set values of advanced options with javascript
        $("#advanced-toggle").click().click();
        if (window.location.search) {
            search_from_parameters(window.location.search.substring(1));
        }
    }

    main();

});
