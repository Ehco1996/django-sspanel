var react = function () {
    if (django.jQuery('#id_node_type').val() === 'ss') {
        django.jQuery('#ss_config-group').show(500);
        django.jQuery('#ray_config-group').hide(500);
        // django.jQuery('#vless_config_group').hide(500);
    }
    if (django.jQuery('#id_node_type').val() === 'ray'){
        django.jQuery('#ss_config-group').hide(500);
        django.jQuery('#ray_config-group').show(500);
        // django.jQuery('#vless_config_group').hide(500);
    }
};

django.jQuery(function () {
    react();
    django.jQuery('#id_node_type').on('change', react);
});