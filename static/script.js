// Open the modal
function openModal(element) {
    var modal = document.getElementById("galleryModal");
    var modalImg = document.getElementById("modalImage");
    var captionText = document.getElementById("caption");
    
    modal.style.display = "block";
    modalImg.src = element.src;
    captionText.innerHTML = element.alt;
  }
  
  // Get the <span> element that closes the modal
  var span = document.getElementsByClassName("close")[0];
  
  // When the user clicks on <span> (x), close the modal
  span.onclick = function() { 
    var modal = document.getElementById("galleryModal");
    modal.style.display = "none";
  }
  