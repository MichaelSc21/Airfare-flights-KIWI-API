var inputFields = document.querySelectorAll('[class*="disappear"]'); 

document.querySelector('[class*="flight_type"]').addEventListener("change", function() {
        // Get selected flight type
        var flightType = this.value;

        // Toggle visibility of return date and nights in destination fields
        if (flightType === "One-way") {
            for (var i = 0; i < inputFields.length; i++) {
                var inputField = inputFields[i];
                inputField.style.display = 'none';
            };
        } else if (flightType === 'Round') {
            for (var i = 0; i < inputFields.length; i++) {
                var inputField = inputFields[i];
                inputField.style.display = 'block';
            };
        };  
    });
