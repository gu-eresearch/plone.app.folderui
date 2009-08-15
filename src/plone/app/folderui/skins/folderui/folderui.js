folderui = new Object(); //namespace

folderui.toggle_facet = function() {
    context = jQuery(this).parent();
    jQuery('.options', context).toggle();
}

folderui.toggle_morefilters = function() {
    context = jQuery(this).parent();
    jQuery('ul.facetmenu', context).toggle();
}

folderui._show_conjunction = function(context) {
    jQuery('div.conjunction_choice', context).show();
}

folderui.show_conjunction = function() {
    context = jQuery(this).parent().parent().parent(); //div.searchfilter
    folderui._show_conjunction(context);
}


folderui.facet_helper = function() {
    jQuery('div.searchfilter h3').bind('click', folderui.toggle_facet);
    jQuery('div.morefilters h4').bind('click', folderui.toggle_morefilters);
    jQuery("div.searchfilter ul.facetmenu input[type='checkbox']").bind('click', folderui.show_conjunction);
    jQuery('div.morefilters ul.facetmenu').hide(); //default:hide, click expands
    jQuery('div.searchfilter div.conjunction_choice').hide(); //hide until checkbox click
    var facetboxes = jQuery('div.searchfilter');
    for (var i=0; i<facetboxes.length; i++) {
        var box = jQuery(facetboxes[i]);
        var checkboxes = jQuery(":checked",  jQuery("ul", box));
        for (var j=0; j<checkboxes.length; j++) {
            var checkbox = checkboxes[j];
            folderui._show_conjunction(jQuery(checkbox).parent().parent().parent());
        }
    }
}

jQuery(document).ready(folderui.facet_helper);

