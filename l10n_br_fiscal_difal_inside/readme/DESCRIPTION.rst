This module adds an alternative calculation mode for the ICMS DIFAL base on
the Brazilian fiscal engine, allowing the base to be
grossed up before the DIFAL and FCP are computed.

In this mode the base is::

    base = goods (including IPI) / (1 - destination rate - FCP rate)

and the taxes follow from it::

    DIFAL = base * (destination rate - interstate rate)
    FCP   = base * FCP rate
    ICMS  = base * interstate rate

which is the same as saying that the base is composed of::

    base = goods + interstate ICMS + DIFAL + FCP

The interstate ICMS is grossed up together with the DIFAL. The two are not
separable: the DIFAL is computed from the difference between the destination
and the interstate rates applied to the grossed up base, so it already assumes
the interstate ICMS was taken from that same base. Leaving the interstate ICMS
on the plain base would credit the destination state less tax than the DIFAL
computation assumed, and the identity above would not hold.

The mode is set per fiscal operation line. By default the standard OCA
behavior (unique/double base by destination state) is preserved.
