"use strict";

$(function () {

    var saved_courses_list = [];
    var saved_courses = {};

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
            history.pushState(null, "Subitize - Course Counts at a Glance", location.origin + "?" + metadata.parameters + location.hash);
            // clear previous search results
            $(".search-results").remove();
            $(".search-result").remove();
            // repopulate search results
            var search_results_heading = $("#search-results-heading h3");
            search_results_heading.html("Search Results (" + results.length + ")");
            populate_search_results(metadata, results);
            enable_more_info_toggle();
            save_saved_courses();
        });
    }

    function populate_search_results(metadata, results) {
        var search_results_heading = $("#search-results-heading");
        if (results.length === 0) {
            return;
        }
        search_results_heading.after(build_search_results_header("search-results", metadata.sorted));
        var search_results_header = $("#search-results-header");
        for (var i = results.length - 1; i >= 0; i -= 1) {
            search_results_header.after(build_course_listing_row(results[i]));
        }
    }

    function build_search_results_header(section, sort) {
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
        return html.join("");
    }

    function build_course_listing_row(result, classnames) {
        var tbody = $("<tbody class=\"data\"></tbody>").append(tr);
        if (classnames === undefined) {
            tbody.addClass("search-result");
        } else {
            for (var i = 0; i < classnames.length; i += 1) {
                tbody.addClass(classnames[i]);
            }
        }
        var tr = $("<tr></tr>");
        tr.append(build_search_result_save_checkbox(result));
        tr.append(build_search_result_semester_cell(result));
        tr.append(build_search_result_course_cell(result));
        tr.append(build_search_result_title_cell(result));
        tr.append(build_search_result_units_cell(result));
        tr.append(build_search_result_instructors_cell(result));
        tr.append(build_search_result_meetings_cell(result));
        tr.append(build_search_result_cores_cell(result));
        tr.append(build_search_result_seats_cell(result));
        tbody.append(tr);
        if (result.info) {
            tbody.append(build_search_result_info_row(result));
        }
        return tbody;
    }

    function build_search_result_save_checkbox(result) {
        var checkbox = $("<input type=\"checkbox\">");
        checkbox.addClass(result.id + "-checkbox");
        if (saved_courses.hasOwnProperty(result.id)) {
            checkbox.prop("checked", "checked");
        }
        checkbox.click(function () {
            save_course_checkbox_handler(checkbox, result);
        });
        return checkbox;
    }

    function build_search_result_semester_cell(result) {
        var html = [];
        var url = "";
        html.push("<td>");
        url = "/";
        url += "?advanced=false";
        url += "&semester=" + result.semester.code;
        html.push("<a href=\"" + url + "\">");
        html.push(result.semester.year + " " + result.semester.season);
        html.push("</a>");
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_course_cell(result) {
        var html = [];
        var url = "";
        html.push("<td>");
        url = "/";
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

    function build_search_result_title_cell(result) {
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

    function build_search_result_units_cell(result) {
        var html = [];
        html.push("<td>");
        html.push(result.units);
        html.push("</td>");
        return html.join("");
    }

    function build_search_result_instructors_cell(result) {
        var html = [];
        var url = "";
        html.push("<td>");
        if (result.instructors.length === 0) {
            html.push("Unassigned");
        } else {
            for (var i = 0; i < result.instructors.length; i += 1) {
                var instructor = result.instructors[i];
                url = "/";
                url += "?advanced=true";
                url += "&semester=" + $("#semester-select").val();
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

    function build_search_result_meetings_cell(result) {
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

    function build_search_result_cores_cell(result) {
        var html = [];
        var url = "";
        html.push("<td>");
        for (var i = 0; i < result.cores.length; i += 1) {
            var core = result.cores[i];
            url = "/";
            url += "?advanced=true";
            url += "&semester=" + result.semester.code;
            url += "&core=" + core.code;
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

    function build_search_result_seats_cell(result) {
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

    function build_saved_courses_table() {
        var saved_courses_separator = $("#saved-courses-separator");
        $("#saved-courses-heading").after(build_search_results_header("saved-courses", null));
        update_saved_courses_display();
    }

    function update_saved_courses_display() {
        $("#saved-courses-heading h3").html("Saved Courses (" + saved_courses_list.length + ")");
        if (saved_courses_list.length === 0) {
            $(".saved-courses").hide();
        } else {
            $(".saved-courses").show();
            saved_courses_list.sort();
            $(".saved-course").remove();
            for (var i = saved_courses_list.length - 1; i >= 0; i -= 1) {
                var course_id = saved_courses_list[i];
                var course = saved_courses[course_id];
                $("#saved-courses-header").after(build_course_listing_row(course, ["saved-course", course.id]));
            }
        }
    }

    function save_course_checkbox_handler(checkbox, result) {
        if (checkbox.prop("checked")) {
            save_course(result);
        } else {
            unsave_course(result);
        }
        update_saved_courses_display();
        save_saved_courses();
    }

    function save_course(result) {
        if (saved_courses.hasOwnProperty(result.id)) {
            return;
        }
        saved_courses_list.push(result.id);
        saved_courses[result.id] = result;
        saved_courses_list.sort();
    }

    function unsave_course(result) {
        if (!saved_courses.hasOwnProperty(result.id)) {
            return;
        }
        saved_courses_list.splice(saved_courses_list.indexOf(result.id), 1);
        delete saved_courses[result.id];
        $("tbody." + result.id).remove();
        $("." + result.id + "-checkbox").prop("checked", false);
    }

    function param(obj) {
        return $.param(obj, false);
    }

    function deparam(str) {
        var obj = {};
        str.replace(/([^=&]+)=([^&]*)/g, function(m, key, value) {
            obj[decodeURIComponent(key)] = decodeURIComponent(value);
        });
        return obj;
    }

    function load_saved_courses() {
        var hash = deparam(location.hash.substring(1));
        if (hash["list"] !== undefined) {
            saved_courses_list = JSON.parse(atob(hash["list"]));
            saved_courses = JSON.parse(atob(hash["dict"]));
            update_saved_courses_display();
            save_saved_courses();
        }
    }

    function save_saved_courses() {
        if (saved_courses_list.length > 0) {
            location.hash = param({
                "list": btoa(JSON.stringify(saved_courses_list)),
                "dict": btoa(JSON.stringify(saved_courses))
            });
        } else {
            location.hash = "";
        }
        // update all links on the page
        $("a").each(function () {
            var a = $(this);
            if (!a.attr("href").startsWith("/")) {
                return;
            }
            var index = a.attr("href").lastIndexOf("#");
            var url = "";
            if (index !== -1) {
                url = a.attr("href").substring(0, index);
            } else {
                url = a.attr("href");
            }
            a.attr("href", url + location.hash);
        });
    }

    function enable_more_info_toggle() {
        var more_info = $(".more-info");
        more_info.click(more_info_click_handler);
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

        // TODO set values of advanced options with javascript
        $("#advanced-toggle").click().click();
        build_saved_courses_table();
        load_saved_courses();
        if (location.search) {
            search_from_parameters(location.search.substring(1));
        }
    }

    main();

});
