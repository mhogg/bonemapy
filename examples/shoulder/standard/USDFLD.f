    SUBROUTINE USDFLD(FIELD,STATEV,PNEWDT,DIRECT,T,CELENT, &
        TIME,DTIME,CMNAME,ORNAME,NFIELD,NSTATV,NOEL,NPT,LAYER, &
        KSPT,KSTEP,KINC,NDI,NSHR,COORD,JMAC,JMATYP,MATLAYO,LACCFLA)

    INCLUDE 'ABA_PARAM.INC'

    CHARACTER :: CMNAME*80, ORNAME*80
    CHARACTER :: FLGRAY(15)*3
    DIMENSION :: FIELD(NFIELD),STATEV(NSTATV),DIRECT(3,3),T(3,3),TIME(2)
    DIMENSION :: ARRAY(15), JARRAY(15), JMAC(*), JMATYP(*), COORD(*)

    ! User variables
    integer, parameter :: chunk_size=1000
    integer :: indx1(1), indx2(1), ios, jrcd, n, elmnum, nintp, num_elems, num_parts
    integer, save :: do_once=0
    real :: huval, density, emodulus, rho_min, rho_max
    real, save :: HUmin, HUmax
    character(len=80) :: partname
    character(len=256) :: outdir, mat_props
    character(len=80), allocatable, save :: parts(:), temp_parts(:)

    ! Define a custom array type that contains multiple arrays of different sizes
    ! Reference: https://stackoverflow.com/questions/18316592/multidimensional-array-with-different-lengths
    ! Custom type for local element numbers per part
    type t_raggedarray_i
        integer, allocatable :: locnum(:)
    end type t_raggedarray_i
    type(t_raggedarray_i), allocatable, save :: elements(:)

    ! Custom type for HU values for each part
    type t_raggedarray_r
        real, allocatable :: vals(:,:)
    end type t_raggedarray_r
    type(t_raggedarray_r), allocatable, save :: HU(:)

    ! Custom type to read mat_props file
    type t_hudata
        character(len=80):: partname
        integer :: elmnum
        integer :: nintp
        real :: huval
    end type t_hudata
    type(t_hudata) :: hudatan
    type(t_hudata), allocatable :: hudata(:), temp_hudata(:)

    ! Solution dependent variables (SDVs) and field variables (FIELDs)
    ! SDV1 = Hounsfield Units (HU)
    ! SDV2 = Bone density (g/cm3)
    ! SDV3, FIELD1 = Elastic modulus (MPa)

    ! Set user variables
    mat_props = 'HUvalues.txt'  ! Filename of file containing HU values
    rho_min   = 0.1             ! Minimum apparent bone density (g/cm3)
    rho_max   = 1.7             ! Maximum apparent bone density (g/cm3)

    ! Do once only:
    ! -------------

    ! Read HU values from material properties file
    if (do_once/=1) then

        do_once = 1

        call GETOUTDIR(outdir, lenoutdir)
        mat_props = trim(adjustl(outdir)) // '/' // mat_props
        open(unit=101, file=mat_props, status='OLD', action='READ')

        readfile: do

            read(101,*,iostat=ios) hudatan

            if (ios/=0) then
                ! NOTE: temp_hudata = hudata(1:n) should work here even without the allocate(temp_hudata(n)),
                ! but crashes during packaging. However, temp_hudata(1:n) does not cause a crash
                if (allocated(temp_hudata)) deallocate(temp_hudata)
                allocate(temp_hudata(n))
                temp_hudata(1:n) = hudata(1:n)
                call move_alloc(from=temp_hudata, to=hudata)
                exit readfile
            end if

            if (allocated(hudata)) then
                if (n == size(hudata)) then
                    allocate(temp_hudata(size(hudata) + chunk_size))
                    temp_hudata(1:size(hudata)) = hudata
                    call move_alloc(from=temp_hudata, to=hudata)
                end if
                n = n + 1
            else
                allocate(hudata(chunk_size))
                n = 1
            end if
            hudata(n) = hudatan

        end do readfile
        close(101)

        ! Get the part names and the number of parts
        allocate(parts(0))
        do i=1,size(hudata)
            partname = upcase(hudata(i)%partname)
            if (any(parts==partname)==.false.) then
                allocate(temp_parts(1:size(parts)+1))
                temp_parts(1:size(parts)) = parts
                temp_parts(size(parts)+1) = partname
                call move_alloc(from=temp_parts, to=parts)
            end if
        end do
        num_parts = size(parts)

        write(*,*) 'Number of parts = ', num_parts

        ! Populate elements and HU arrays for the current part
        ! Note: We are assuming 4 integration points per element, which only works for the
        !       C3D10 quadratic tet element family
        allocate(elements(num_parts), HU(num_parts))
        do i=1,num_parts

            ! First get the number of elements per part to size the array
            num_elems = 0
            do j=1,size(hudata)
                partname = upcase(hudata(j)%partname)
                if (partname==parts(i) .and. hudata(j)%nintp==1) num_elems = num_elems + 1
            end do
            allocate(elements(i)%locnum(num_elems), HU(i)%vals(num_elems,4))

            write(*,*) 'Number of elements for part ', trim(parts(i)), ' = ', num_elems

            n = 0
            do j=1,size(hudata)

                partname = upcase(hudata(j)%partname)
                elmnum   = hudata(j)%elmnum
                nintp    = hudata(j)%nintp
                huval    = hudata(j)%huval

                if (partname==parts(i)) then
                    if (nintp==1) n = n + 1
                    elements(i)%locnum(n) = elmnum
                    HU(i)%vals(n,nintp) = huval
                end if

            end do

        end do

        ! Get the HU range (HUmin, HUmax)
        HUmin = hudata(1)%huval
        HUmax = hudata(1)%huval
        do i=2,size(hudata)
            huval = hudata(i)%huval
            if (huval<HUmin) HUmin=huval
            if (huval>HUmax) HUmax=huval
        end do
        write(*,*) 'HUmin = ', HUmin
        write(*,*) 'HUmax = ', HUmax

    endif

    ! Do in first increment only:
    ! ---------------------------

    if (KSTEP==1 .and. KINC<=1) then

        ! Get the HU value and place in STATEV(1)
        ! Calculate the apparent bone density from HU and place in STATEV(2)
        ! Calculate bone elastic modulus from density and place in STATEV(3)
        ! Notes:
        ! - Only need to do this in the first increment, because bone properties
        !   do not change
        ! - Convert between part element number and internal element number
        !   Note that internal (global) element number passed into subroutine
        !   as NOEL, but HU values in terms of part (local) element number
        call GETPARTINFO(NOEL, 1, partname, locnum, jrcd)
        if (jrcd==1) write(*,*) 'Error converting from global to local element numbering'
        indx1 = findloc(parts, partname)
        indx2 = findloc(elements(indx1(1))%locnum, locnum)
        huval = HU(indx1(1))%vals(indx2(1),NPT)
        density = HUtoAppDensity(huval,HUmin,HUmax,rho_min,rho_max)
        emodulus = EfromAppDensity(density,2)

        STATEV(1) = huval
        STATEV(2) = density
        STATEV(3) = emodulus

    end if

    ! For all increments:
    ! -------------------

    ! Set field viarable 1, FIELD(1), to the value of the elastic modulus stored in STATEV(3)
    FIELD(1) = STATEV(3)

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
