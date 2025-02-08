$(document).ready(function() {
    $("#start-crawl").click(function() {
        let urls = $("#urls").val().split("\n").map(url => url.trim()).filter(url => url);

        if (urls.length === 0) {
            alert("Please enter at least one URL.");
            return;
        }

        console.log("Sending URLs:", urls);  // Debugging in browser console
        $("#status").text("Crawling in progress...");

        $.ajax({
            url: "/crawl",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ urls: urls }),
            success: function(response) {
                console.log("API Response:", response);  // Debugging
                $("#status").text(response.message);
                $("#download-csv").show();
            },
            error: function(xhr, status, error) {
                console.log("Error:", xhr.responseText);  // Debugging
                $("#status").text("Error occurred while crawling.");
            }
        });
    });

    $("#download-csv").click(function() {
        window.location.href = "/download";
    });
});
