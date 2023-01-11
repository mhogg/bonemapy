    subroutine vusdfld(nblock, nstatev, nfieldv, nprops, ndir, nshr, jElem, &
        kIntPt, kLayer, kSecPt, stepTime, totalTime, dt, cmname, coordMp,   &
        direct, T, charLength, props, stateOld, stateNew, field)

    include 'vaba_param.inc'

    dimension jElem(nblock), coordMp(nblock,*), direct(nblock,3,3), &
              T(nblock,3,3), charLength(nblock), props(nprops),     &
              stateOld(nblock,nstatev), stateNew(nblock,nstatev),   &
              field(nblock,nfieldv)
    character*80 cmname

    ! User variables
    integer, parameter :: chunk_size=1000
    integer :: indx1(1), indx2(1), ios, jrcd, n, elmnum, nintp, num_elems, num_parts
    integer, save :: do_once=0
    real, parameter :: sdv1_flag=1.0
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
    ! SDV1 = Flag used to test if material properties have been applied
    ! SDV2 = Hounsfield Units (HU)
    ! SDV3 = Bone density (g/cm3)
    ! SDV4, FIELD1 = Elastic modulus (MPa)

    ! Set user variables
    mat_props = 'HUvalues.txt'  ! Filename of file containing HU values
    rho_min   = 0.1             ! Minimum apparent bone density (g/cm3)
    rho_max   = 1.7             ! Maximum apparent bone density (g/cm3)

    ! Do once only on first call to subrouine
    if (do_once/=1) then

        do_once = 1

        ! Read the HUvalues.txt file
        ! Reference: https://degenerateconic.com/dynamically-sizing-arrays.html
        call VGETOUTDIR(outdir, lenoutdir)
        mat_props = trim(adjustl(outdir)) // '/' // mat_props
        open(unit=101, file=mat_props, status='OLD', action='READ')

        n = 0
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

    end if

    ! Set the field of the material points. Note that:
    ! - A block of elements are processed together, where nblock is the number of elements in the block. Typically nblock=144.
    ! - For each call of the subroutine, the integration point number kIntPt is the same for all elements in the block.
    ! - jElem is an array of element numbers for the block, so jElem(k) is the (global, or internal) element number
    ! - stateOld will typically be initialised to 0.0, so this can be used as a flag to determine if material properties
    !   have already been set for that material point
    ! - Ensure that all allocatable arrays used within this section are using the save parameter. Otherwise, will get an error
    !   on the second call of the subroutine, as the array data will be lost
    do k=1, nblock

        if (stateOld(k,1)/=sdv1_flag) then
            intnum = jElem(k)
            call VGETPARTINFO(intnum, 1, partname, locnum, jrcd)
            if (jrcd==1) write(*,*) 'Error converting from global to local element numbering'
            indx1 = findloc(parts, partname)
            indx2 = findloc(elements(indx1(1))%locnum, locnum)
            huval = HU(indx1(1))%vals(indx2(1),kIntPt)
            density = HUtoAppDensity(huval,HUmin,HUmax,rho_min,rho_max)
            emodulus = EfromAppDensity(density,2)
        else
            huval = stateOld(k,2)
            density = stateOld(k,3)
            emodulus = stateOld(k,4)
        end if
        stateNew(k,1) = sdv1_flag
        stateNew(k,2) = huval
        stateNew(k,3) = density
        stateNew(k,4) = emodulus
        field(k,1)    = emodulus

    end do

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
