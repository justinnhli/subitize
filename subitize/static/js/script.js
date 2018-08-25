/* globals $ */
"use strict";

$(function () {

    var PROPERTY_OPTION_MAP = {
        ["semester", "#semesters-select"],
        ["instructor", "#instructors-select"],
        ["core", "#cores-select"],
        ["unit", "#units-select"],
        ["department", "#departments-select"],
        ["lower", "#lower"],
        ["upper", "#upper"],
        ["start_hour", "#start-hours-select"],
        ["end_hour", "#end-hours-select"],
    }

    var option_defaults = null;
    var state = {
        search: {
        },
        gui: {
            show_options: false,
            tab: "search-results"
        },
        data: {
            saved_offerings: {}
        }
    };
    var offering_data = {};

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
        state = JSON.parse(decodeURI(get_url_hash()));
        apply_state();
    }

    function save_state() {
        var url = location.origin;
        url += "#" + encodeURI(JSON.stringify(state));
        history.pushState(null, "Subitize - Course Counts at a Glance", url);
        if ($("#semesters-select").val() !== "") {
            state.search.semester = $("#semesters-select").val();
        }
        if ($("#instructors-select").val() !== "") {
            state.search.instructor = $("#instructors-select").val();
        }
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
                $(option).val(option_defaults[property]);
            }
        }
    }

    // POPULATION SEARCH OPTIONS

    function load_option_defaults() {
        return $.get("defaults").done(function(response) {
            option_defaults = response;
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

    function search() {
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

    // MAIN

    function main() {

        show_tab(state.gui.tab);

        // set up GUI events
        $("#options-toggle").click(toggle_search_options);
        $(".search-option").change(function () {
            var option = $(this);
            state.search[option.attr("name")] = option.val();
            save_state();
        });
        $("#saved-courses-heading").click(function () {
            show_tab("saved-courses");
            save_state();
        });
        $("#search-results-heading").click(function () {
            show_tab("search-results");
            save_state();
        });

        // populate search options, then 
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
    }

    main();

});
