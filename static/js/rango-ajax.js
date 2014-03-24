$(document).ready(function(){
  
  $("#likes").click(function(e){
    var catid = $(this).attr("data-catid");
    $.get('/rango/like_category/', {category_id: catid }, function(data){
      $("#like_count").html(data);
      $("#likes").hide();
    });
  });

  $("#suggestion").keyup(function(){
    var query = $(this).val();
    $.get('/rango/suggest_category/', {query:query}, function(data){
      $("#cats").html(data);
    });
  });

  $(".rango-add").click(function(){
    var cat_id = $(this).attr("data-catid");
    var title = $(this).attr("data-title");
    var url = $(this).attr("data-url");
    $(this).hide();
    $.get('/rango/auto_add_page', {cat_id: cat_id, title: title, url: url}, function(data){
      $("#pages").html(data);
    });
  });
});
