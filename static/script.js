$(document).ready(function () {
    console.log("✅ script.js loaded successfully");

    // 🔹 Upload CSV button
    $("#upload-csv").click(function () {
        let file = $("#csvFile")[0].files[0];
        if (!file) {
            alert("Please select a CSV file first!");
            return;
        }

        if (!file.name.endsWith(".csv")) {
            alert("Please upload a .csv file (not Excel .xlsx).");
            return;
        }

        let formData = new FormData();
        formData.append("file", file);

        $("#status").text("Uploading and processing...");
        $(".loader").show();
        $(this).prop("disabled", true);

        $.ajax({
            url: "/upload",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                console.log("✅ Upload response:", response);
                $("#status").text(response.message || "Upload complete!");
                $(".loader").hide();
                $("#download-csv").show();
                $("#upload-csv").prop("disabled", false);
            },
            error: function (xhr) {
                console.log("❌ Upload error:", xhr.responseText);
                $("#status").text("Error uploading CSV.");
                $(".loader").hide();
                $("#upload-csv").prop("disabled", false);
            }
        });
    });

    // 🔹 Start Exploring button
    $("#start-crawl").click(function () {
        let urls = $("#urls").val().split("\n").map(url => url.trim()).filter(url => url);

        if (urls.length === 0) {
            alert("Please enter at least one URL or upload a CSV.");
            return;
        }

        console.log("🚀 Sending URLs:", urls);
        $("#status").text("Exploring in progress...");
        $(".loader").show();
        $(this).prop("disabled", true);

        $.ajax({
            url: "/explore",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ urls }),
            success: function (response) {
                console.log("✅ API Response:", response);
                $("#status").text(response.message || "Exploration complete!");
                $(".loader").hide();
                $("#download-csv").show();
                $("#start-crawl").prop("disabled", false);
            },
            error: function (xhr) {
                console.log("❌ Error:", xhr.responseText);
                $("#status").text("Error occurred while exploring.");
                $(".loader").hide();
                $("#start-crawl").prop("disabled", false);
            }
        });
    });

    // 🔹 Download CSV
    $("#download-csv").click(function () {
        window.location.href = "/download";
    });

    // 🔹 Show file name when selected
    $("#csvFile").change(function () {
        let file = this.files[0];
        if (file) {
            $("#file-name").text("File selected: " + file.name).show();
        } else {
            $("#file-name").hide();
        }
    });
});
