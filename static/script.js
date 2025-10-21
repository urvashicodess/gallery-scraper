$(document).ready(function() {
    $("#start-crawl").click(function() {
        let urls = $("#urls").val().split("\n").map(url => url.trim()).filter(url => url);

        if (urls.length === 0) {
            alert("Please enter at least one URL.");
            return;
        }

        console.log("Sending URLs:", urls);
        $("#status").text("Exploring in progress...");
        $(".loader").show();
        $(this).prop("disabled", true);

        $.ajax({
            url: "/explore",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ urls }),
            success: function(response) {
                console.log("API Response:", response);
                $("#status").text(response.message || "Download ready!");
                $(".loader").hide();
                $("#download-csv").show();
                $("#start-crawl").prop("disabled", false);
            },
            error: function(xhr) {
                console.log("Error:", xhr.responseText);
                $("#status").text("Error occurred while crawling.");
                $(".loader").hide();
                $("#start-crawl").prop("disabled", false);
            }
        });
    });

    $("#download-csv").click(function() {
        window.location.href = "/download";
    });

    // Optional: update filename when user selects CSV
    $("#csvFile").change(function() {
        let file = this.files[0];
        if (file) {
            $("#file-name").text("File selected: " + file.name).show();
        } else {
            $("#file-name").hide();
        }
    });
});