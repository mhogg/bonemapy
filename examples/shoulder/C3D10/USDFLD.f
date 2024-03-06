    SUBROUTINE USDFLD(FIELD,STATEV,PNEWDT,DIRECT,T,CELENT, &
        TIME,DTIME,CMNAME,ORNAME,NFIELD,NSTATV,NOEL,NPT,LAYER, &
        KSPT,KSTEP,KINC,NDI,NSHR,COORD,JMAC,JMATYP,MATLAYO,LACCFLA)

    INCLUDE 'ABA_PARAM.INC'

    CHARACTER :: CMNAME*80, ORNAME*80, CPNAME*80, OUTDIR*256
    CHARACTER :: FLGRAY(15)*3
    DIMENSION :: FIELD(NFIELD),STATEV(NSTATV),DIRECT(3,3),T(3,3),TIME(2)
    DIMENSION :: ARRAY(15), JARRAY(15), JMAC(*), JMATYP(*), COORD(*)

    ! User variables
    INTEGER, PARAMETER :: minel=1, maxel=123418, nparts=1, num_intpts=4
    INTEGER :: elmnum, nintp, ios, do_once=0, flag=0
    REAL :: huval, rho_min, rho_max
    REAL, SAVE :: HU(nparts,minel:maxel,num_intpts), HUmin, HUmax
    CHARACTER(len=256) :: mat_props
    CHARACTER(len=80)  :: parts(nparts), partname, partnameUC

    ! Variables
    ! STATEV(1) = Hounsfield Units (HU)
    ! STATEV(2) = Bone density (g/cm3)
    ! FIELD(1)  = Young's modulus (MPa)

    ! Set user variables
    parts(1)  = 'scapula'       ! Name of part
    mat_props = 'HUvalues.txt'  ! Filename of file containing HU values
    rho_min   = 0.1             ! Minimum apparent bone density (g/cm3)
    rho_max   = 1.7             ! Maximum apparent bone density (g/cm3)

    ! Do once only:
    ! -------------

    ! Read HU values from material properties file
    if (do_once/=1) then

        CALL GETOUTDIR(OUTDIR, LENOUTDIR)
        mat_props = trim(adjustl(OUTDIR)) // '/' // mat_props

        open(unit=101, file=mat_props, status='OLD')

        readfile: do
        
            read(101,*,iostat=ios) partname, elmnum, nintp, huval
            if (ios/=0) exit readfile

            if (flag==0) then
                HUmin = huval
                HUmax = huval
                flag  = 1
            end if

            if (huval<HUmin) HUmin=huval
            if (huval>HUmax) HUmax=huval

            do i=1,nparts
                if (upcase(partname)==upcase(parts(i))) HU(i,elmnum,nintp)=huval
            end do

        end do readfile

        write(*,*) 'HUmin = ', HUmin
        write(*,*) 'HUmax = ', HUmax
        write(7,*) 'HUmin = ', HUmin
        write(7,*) 'HUmax = ', HUmax

        close(101)
        do_once = 1

    endif

    ! Do in first increment only:
    ! ---------------------------

    if (KSTEP==1 .and. KINC<=1) then

        ! Convert between part element number and internal element number
        ! Note that internal (global) element number passed into subroutine
        ! as NOEL, but HU values in terms of part (local) element number
        CALL GETPARTINFO(NOEL, 1, CPNAME, LOCNUM, JRCD)

        if (JRCD==1) THEN
            write(*,*) 'Error converting from global to local numbering'
            write(7,*) 'Error converting from global to local numbering'
        end if

        do i=1,nparts
            partnameUC = upcase(parts(i))
            if (CPNAME==partnameUC) then
                STATEV(1) = HU(i,LOCNUM,NPT)
            end if
        end do

        ! Calculate the apparent bone density from HU and place in STATEV(2)
        STATEV(2) = HUtoAppDensity(real(STATEV(1)),HUmin,HUmax,rho_min,rho_max)

    end if

    ! For all steps:
    ! --------------

    ! Calculate bone elastic modulus from density and place in FIELD(1)
    FIELD(1) = EfromAppDensity(real(STATEV(2)),1)

    ! --------------

    ! User defined functions
    contains

    function upcase(string) result(upper)
    character(len=*), intent(in) :: string
    character(len=len(string)) :: upper
    integer :: j
        do j = 1,len(string)
            if(string(j:j) >= "a" .and. string(j:j) <= "z") then
                upper(j:j) = achar(iachar(string(j:j)) - 32)
        else
            upper(j:j) = string(j:j)
        end if
    end do
    end function upcase

    ! --------------

    function HUtoAppDensity(huval,humin,humax,rhomin,rhomax) result(appdensity)
    real, intent(in)  :: huval,humin,humax,rhomin,rhomax
    real :: appdensity

    ! Linearly converts the HU to apparent density with the following limits:
    ! rho = rhomin at humin
    ! rho = rhomax at humax

    appdensity = rhomin + (rhomax-rhomin)*((huval-humin)/(humax-humin))

    end function HUtoAppDensity

    ! --------------

    function EfromAppDensity(appdensity,choice) result(Evalue)
    real, intent(in) :: appdensity
    real :: Evalue, snrate
    integer, intent(in) :: choice

    ! Converts from apparent bone density (g/cm3) to Elastic Modulus (MPa)
    ! A number of relationships can be used, depending on the value of "choice":
    ! (1) Carter and Hayes, 1977
    ! (2) Morgan et al, 2003

    select case(choice)
    case (1)
        snrate = 0.01
        Evalue = 3790*(snrate**0.06)*(appdensity**3)
    case (2)
        Evalue = 6950*(appdensity**1.49)
    end select

    end function EfromAppDensity

    ! --------------

    end