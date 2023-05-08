$(document).ready(function() {
    var button = $(".dropdown-toggle");
    var table = $(".dates_checked ");

    $(".dropdown-toggle").on('click', function() {
      $(this).siblings(".dates_checked").slideToggle(); 
    });
  });

  
$(document).ready(function() {
    // Add event listener to all buttons
    $(".btn-function").on('click', function() {
      // Get the text content of the button
      var buttonText = $(this).text();

      // Check which button was clicked
      if (buttonText == "Plot graph" || buttonText == "Plot graph with line of best fit") {
        // Get the selected row data
        var selectedRow = $(".table tr.selected-tr");

        // Check if a row is selected
        if (selectedRow.length === 1) {
          // Extract data from selected row
          var timeChecked = selectedRow.find("td").eq(0).text();
          var fileStart = selectedRow.find("td").eq(1).text();
          var fileEnd = selectedRow.find("td").eq(2).text();

          // Send GET request to /show_data with extracted data
          $.get('/show_data', {
            'time_checked': timeChecked,
            'file_start': fileStart,
            'file_end': fileEnd
          }, function(data) {
            // Handle response from server if necessary
          });
        }
        else {
            alert('You can only select 1 file for this function')
        }
      } 

      else if (buttonText == "Compare data from 2 files") {
        // Get the selected rows data
        var selectedRows = $(".table tbody tr.selected-tr");

        // Check if two rows are selected
        if (selectedRows.length === 2) {
          // Extract data from selected rows
          var timeChecked1 = selectedRows.eq(0).find("td").eq(0).text();
          var fileStart1 = selectedRows.eq(0).find("td").eq(1).text();
          var fileEnd1 = selectedRows.eq(0).find("td").eq(2).text();
          var timeChecked2 = selectedRows.eq(1).find("td").eq(0).text();
          var fileStart2 = selectedRows.eq(1).find("td").eq(1).text();
          var fileEnd2 = selectedRows.eq(1).find("td").eq(2).text();

          // Send GET request to /show_data with extracted data
          $.get('/show_data', {
            'time_checked_1': timeChecked1,
            'file_start_1': fileStart1,
            'file_end_1': fileEnd1,
            'time_checked_2': timeChecked2,
            'file_start_2': fileStart2,
            'file_end_2': fileEnd2
          }, function(data) {
            // Handle response from server if necessary
          });
        }
      }
    });

    // Add event listener to all table rows
    $(".table tbody tr").on('click', function() {
        // Deselect all other rows
        //$(this).siblings().removeClass("selected-tr");
        var countSelectedRows = document.querySelectorAll('.selected-tr').length;
        if (countSelectedRows > 1) {
            alert('You can select at the very most 2 files')
        }
        else {
            // Toggle selected class for clicked row
            $(this).toggleClass("selected-tr");
        }


        

    });
  });
