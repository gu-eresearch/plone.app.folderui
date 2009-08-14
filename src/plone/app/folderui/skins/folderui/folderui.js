
function toggle_facet() {
    context = jQuery(this).parent();
    jQuery('.options', context).toggle();
}

function toggle_morefilters() {
    context = jQuery(this).parent();
    jQuery('ul.facetmenu', context).toggle();
}


function facet_helper() {
    jQuery('div.searchfilter h3').bind('click', toggle_facet);
    jQuery('div.morefilters h4').bind('click', toggle_morefilters);
    jQuery('div.morefilters ul.facetmenu').hide(); //default:hide, click expands
    /* jQuery('div.searchfilter ul').toggle(); */
}

jQuery(document).ready(facet_helper);

